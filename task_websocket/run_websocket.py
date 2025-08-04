#!/usr/bin/env python3
import asyncio
import websockets
import json
import os
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry


class WebSocketServer:

    def __init__(self):
        self.config = self.load_config()
        self.registry = Registry(self.get_db_name())

    def load_config(self):
        from odoo.tools import config
        config_file = '/etc/odoo/odoo.conf' if os.path.exists(
            '/etc/odoo/odoo.conf') else '/opt/odoo16/odoo/conf/odoo.conf'
        config.parse_config(['-c', config_file])
        return config

    def get_db_name(self):
        if hasattr(self.config, 'websocket_16') and self.config.db_name:
            return self.config.db_name
        from odoo.service.db import list_dbs
        dbs = list_dbs()
        if not dbs:
            raise Exception("No databases available")
        return dbs[0]

    async def handle_connection(self, websocket):
        """Handle a new websocket connection"""
        print(f"New connection from {websocket.remote_address}")
        try:
            async for message in websocket:
                print(f"Received message: {message}")
                response = await self.process_message(message)
                if response:
                    await websocket.send(json.dumps(response))
        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await websocket.send(json.dumps({"error": str(e)}))

    async def process_message(self, message):
        """Process each message with a fresh cursor"""
        try:
            data = json.loads(message)
            if data.get('action') == 'register':
                return await self.handle_registration(data)
            return {"status": "error", "message": "Invalid action"}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def handle_registration(self, data):
        """Handle registration message"""
        with self.registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            sender_id = data.get('sender_id')
            if not sender_id:
                return {"status": "error", "message": "sender_id required"}

            employee = env['hr.employee'].search(
                [('sender_id', '=', sender_id)], limit=1)
            if not employee:
                return {"status": "error", "message": "Employee not found"}

            tasks = env['project.task'].search([
                ('member_ids', 'in', employee.id),
                ('notified_member_ids', 'not in', employee.id)
            ])

            task_list = []
            for task in tasks:
                task_list.append(self.format_task(task))
                task.write({'notified_member_ids': [(4, employee.id)]})

            return {
                "status": "success",
                "employee": employee.name,
                "tasks": task_list,
                "count": len(task_list)
            }

    def format_task(self, task):
        """Format task data for response"""
        return {
            'id': task.id,
            'name': task.name,
            'description': task.description or '',
            'members': [m.name for m in task.member_ids],
            'created_at': task.create_date.isoformat() if task.create_date else None
        }


async def main():
    server = WebSocketServer()
    async with websockets.serve(server.handle_connection, "0.0.0.0", 8766):
        print("WebSocket server started on ws://0.0.0.0:8766")
        await asyncio.Future()  # Run forever


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped")