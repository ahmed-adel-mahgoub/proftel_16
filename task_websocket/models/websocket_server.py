import asyncio
import websockets
import json
import threading
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class WebsocketServer(models.Model):
    _name = 'websocket.server'
    _description = 'Websocket Notification Server'

    active = fields.Boolean(default=True)
    port = fields.Integer(default=8766)
    host = fields.Char(default='0.0.0.0')

    _clients = {}
    _server_thread = None
    _loop = None
    _server = None

    def start_server(self):
        """Start the websocket server in a separate thread"""
        if self._server_thread and self._server_thread.is_alive():
            _logger.info("Server already running")
            return

        def run_server():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            async def server_task():
                self._server = await websockets.serve(
                    self.handle_connection,
                    self.host,
                    self.port,
                    ping_interval=20,
                    ping_timeout=20
                )
                _logger.info(f"Server started on {self.host}:{self.port}")
                await self._server.wait_closed()

            self._loop.run_until_complete(server_task())

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        _logger.info("Server thread started")

    async def handle_connection(self, websocket, path):
        """Handle a new websocket connection"""
        sender_id = None
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('action') == 'register':
                        sender_id = data.get('sender_id')
                        if sender_id:
                            self._clients[sender_id] = websocket
                            _logger.info(f"Client registered: {sender_id}")
                            await self.send_pending_tasks(sender_id)
                except json.JSONDecodeError:
                    _logger.error(f"Invalid JSON: {message}")
        except websockets.exceptions.ConnectionClosed:
            _logger.info(f"Connection closed for {sender_id}")
        finally:
            if sender_id in self._clients:
                del self._clients[sender_id]
                _logger.info(f"Client unregistered: {sender_id}")

    async def send_pending_tasks(self, sender_id):
        """Send all pending tasks to a specific client"""
        if sender_id not in self._clients:
            return

        employee = self.env['hr.employee'].search([
            ('sender_id', '=', sender_id)
        ], limit=1)
        if not employee:
            return

        tasks = self.env['project.task'].search([
            ('member_ids', 'in', employee.id),
            ('notified_member_ids', 'not in', employee.id)
        ])

        for task in tasks:
            await self.send_task_notification(employee, task)

    async def send_task_notification(self, employee, task):
        """Send a single task notification"""
        if employee.sender_id not in self._clients:
            return

        websocket = self._clients[employee.sender_id]
        task_data = {
            'type': 'task_update',
            'id': task.id,
            'name': task.name,
            'description': task.description or '',
            'stage': task.stage_id.name if task.stage_id else '',
            'action': 'create' if task.create_date == task.write_date else 'update'
        }

        try:
            await websocket.send(json.dumps(task_data))
            task.write({'notified_member_ids': [(4, employee.id)]})
            _logger.info(f"Sent task {task.id} to {employee.name}")
        except Exception as e:
            _logger.error(f"Failed to send task: {e}")

    def notify_task_update(self, task, action='update'):
        """Called from Odoo when a task changes"""
        if not self._loop or not self._server:
            _logger.warning("Server not ready")
            return

        # Run in the websocket thread
        asyncio.run_coroutine_threadsafe(
            self._notify_task_update(task, action),
            self._loop
        )

    async def _notify_task_update(self, task, action):
        """Async notification handler"""
        for member in task.member_ids:
            if member.sender_id and member.sender_id in self._clients:
                await self.send_task_notification(member, task)