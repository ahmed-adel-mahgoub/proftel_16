import asyncio
import websockets
import json
import threading
from odoo import models, fields, api


class WebsocketServer(models.Model):
    _name = 'websocket.server'
    _description = 'Websocket Notification Server'

    active = fields.Boolean(default=True)
    port = fields.Integer(default=8766, string='Port Number')
    host = fields.Char(default='0.0.0.0', string='Host Address')

    _clients = {}  # Format: {sender_id: websocket}
    _server_thread = None
    _loop = None

    def start_server(self):
        """Start the websocket server in a separate thread"""
        if self._server_thread and self._server_thread.is_alive():
            return

        def run_server():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

            start_server = websockets.serve(
                self.handle_connection,
                self.host,
                self.port
            )

            self._loop.run_until_complete(start_server)
            self._loop.run_forever()

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()

    async def handle_connection(self, websocket, path):
        """Handle incoming websocket connections"""
        try:
            async for message in websocket:
                data = json.loads(message)
                if data.get('action') == 'register':
                    sender_id = data.get('sender_id')
                    if sender_id:
                        self._clients[sender_id] = websocket
                        await self.send_pending_tasks(sender_id, websocket)
        finally:
            # Remove client when connection closes
            for sender_id, ws in list(self._clients.items()):
                if ws == websocket:
                    self._clients.pop(sender_id)
                    break

    async def send_pending_tasks(self, sender_id, websocket):
        """Send all pending tasks for this employee"""
        employee = self.env['hr.employee'].search(
            [('sender_id', '=', sender_id)], limit=1)
        if not employee:
            return

        tasks = self.env['project.task'].search([
            ('member_ids', 'in', employee.id),
            ('notified_member_ids', 'not in', employee.id)
        ])

        for task in tasks:
            await self.send_task(employee, task, websocket)

    async def send_task(self, employee, task, websocket):
        """Send a single task to the client"""
        task_data = {
            'id': task.id,
            'name': task.name,
            'description': task.description or '',
            'members': [m.name for m in task.member_ids],
            'created_at': task.create_date.isoformat() if task.create_date else None
        }

        try:
            await websocket.send(json.dumps(task_data))
            task.write({'notified_member_ids': [(4, employee.id)]})
        except Exception as e:
            print(f"Failed to send task to {employee.name}: {e}")

    def notify_new_tasks(self, tasks):
        """Notify about new tasks to relevant clients"""
        if not self._loop:
            return

        asyncio.run_coroutine_threadsafe(
            self._notify_new_tasks(tasks),
            self._loop
        )

    async def _notify_new_tasks(self, tasks):
        """Async task to notify about new tasks"""
        for task in tasks:
            for member in task.member_ids:
                if member.sender_id and member.sender_id in self._clients:
                    await self.send_task(member, task,
                                         self._clients[member.sender_id])

    def notify_updated_tasks(self, tasks):
        """Notify about updated tasks to relevant clients"""
        if not self._loop:
            return

        asyncio.run_coroutine_threadsafe(
            self._notify_updated_tasks(tasks),
            self._loop
        )

    async def _notify_updated_tasks(self, tasks):
        """Async task to notify about updated tasks"""
        for task in tasks:
            for member in task.member_ids:
                if member.sender_id and member.sender_id in self._clients:
                    await self.send_task(member, task,
                                         self._clients[member.sender_id])