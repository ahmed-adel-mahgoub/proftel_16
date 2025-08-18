import asyncio
import uuid

import websocket
import websockets
from websocket import WebSocketTimeoutException, WebSocketConnectionClosedException
from odoo import models, fields, api,_
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import json
import logging

_logger = logging.getLogger(__name__)


class WebsocketClients(models.Model):
    _name = 'websocket.clients'
    _description = 'WebSocket Connected Clients'
    _order = 'connected_at desc'

    client_id = fields.Char(string='Client ID', required=True, index=True)
    name = fields.Char(string='Client Name')
    employee_id = fields.Many2one('hr.employee',string='Employee')
    department_id = fields.Char(related='employee_id.department_id.name',
                                string='Department'
                                , readonly=True)
    connected_at = fields.Datetime(string='Connected At'
                                   , default=fields.Datetime.now)
    disconnected_at = fields.Datetime(string='Disconnected At')
    ip_address = fields.Char(string='IP Address')
    path = fields.Char(string='Connection Path')
    is_active = fields.Boolean(string='Is Active', default=True)
    last_activity = fields.Datetime(string='Last Activity')
    sender_id = fields.Char(string='Sender ID', index=True)

    def update_activity(self):
        """Update the last activity timestamp"""
        self.write({'last_activity': fields.Datetime.now()})

    def cleanup_inactive(self, days=1):
        """Cleanup old inactive connections"""
        deadline = fields.Datetime.now() - timedelta(days=days)
        return self.search([
            ('is_active', '=', False),
            ('disconnected_at', '<', deadline)
        ]).unlink()


    # def send_message_to_client(self, client_id, message):
    #     self.ensure_one()
    #     try:
    #         websocket_url = self.env['ir.config_parameter'].sudo().get_param(
    #             'websocket.server.url', 'ws://localhost:8765')
    #
    #         async def async_send():
    #             async with websockets.connect(
    #                     websocket_url,
    #                     ping_interval=20,
    #                     ping_timeout=20,
    #                     close_timeout=20
    #             ) as websocket:
    #                 # Identify as Odoo and send message
    #                 full_message = {
    #                     'sender': 'odoo',
    #                     'target_client': client_id,
    #                     'payload': message
    #                 }
    #                 await websocket.send(json.dumps(full_message))
    #
    #                 # Wait for acknowledgment
    #                 ack = await asyncio.wait_for(websocket.recv(), timeout=10)
    #                 ack_data = json.loads(ack)
    #                 return ack_data.get('status') == 'success'
    #
    #         loop = asyncio.new_event_loop()
    #         asyncio.set_event_loop(loop)
    #         try:
    #             return loop.run_until_complete(async_send())
    #         finally:
    #             loop.close()
    #     except Exception as e:
    #         _logger.error("WebSocket error: %s", str(e), exc_info=True)
    #         return False
    def send_message_to_client(self, client_id, message):
        self.ensure_one()
        try:
            websocket_url = self.env['ir.config_parameter'].sudo().get_param(
                'websocket.server.url', 'ws://localhost:8765')

            async def async_send():
                async with websockets.connect(
                        websocket_url,
                        ping_interval=20,
                        ping_timeout=20,
                        close_timeout=20
                ) as websocket:
                    # Include sender_id in the full message
                    full_message = {
                        'sender': 'odoo',
                        'sender_id': message.get('sender_id', ''),
                        'target_client': client_id,
                        'payload': message
                    }
                    await websocket.send(json.dumps(full_message))

                    # Wait for acknowledgment
                    ack = await asyncio.wait_for(websocket.recv(), timeout=10)
                    ack_data = json.loads(ack)
                    return ack_data.get('status') == 'success'

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_send())
            finally:
                loop.close()
        except Exception as e:
            _logger.error("WebSocket error for client %s (Sender: %s): %s",
                          client_id, message.get('sender_id', 'none'), str(e), exc_info=True)
            return False

    def delete_inactive_clients(self):
        """Delete all inactive client records"""
        inactive_clients = self.search([('is_active', '=', False)])
        inactive_clients.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Deleted %s inactive clients') % len(
                    inactive_clients),
                'sticky': False,
                'type': 'success',
            }
        }