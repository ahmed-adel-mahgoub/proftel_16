import time
from odoo.release import version
odoo_version = version
from odoo import models, fields, api
from odoo.exceptions import UserError
import websockets
import asyncio
import json
import logging
_logger = logging.getLogger(__name__)


class CheckAttendance(models.Model):
    _inherit = 'check.attendance'

    websocket_client_id = fields.Many2one(
        'websocket.clients',
        string='WebSocket Client',
        domain="[('is_active', '=', True)]"
    )
    sender_id = fields.Char(
        string='Sender ID',
        help="The ID used to identify this record in WebSocket communications",
        related="websocket_client_id.sender_id"
    )

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if not record.sender_id:
            record.sender_id = record.id
        return record

    def _send_websocket_message(self, message):
        """Helper method to send WebSocket messages"""
        try:
            # Get the WebSocket server URL from system parameters
            websocket_url = self.env['ir.config_parameter'].sudo().get_param(
                'websocket.server.url',
                'ws://localhost:8765'
            )

            async def async_send():
                async with websockets.connect(websocket_url) as websocket:
                    await websocket.send(json.dumps(message))
                    response = await websocket.recv()
                    return json.loads(response)

            # Run the async function synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(async_send())
            loop.close()
            return response

        except Exception as e:
            raise UserError(f"WebSocket communication error: {str(e)}")


    def action_send_via_websocket(self):
        self.ensure_one()
        if not self.websocket_client_id:
            raise UserError("No WebSocket client configured")

        # Prepare message
        message = {
            "action": "listen_attendance",
            "data": [{
                "name": self.name,
                "check_in": self.check_in.isoformat() if self.check_in else None,
                "employee_id": self.employee_id.id if self.employee_id else None,
                "employee_email": self.employee_email,
                "check_in_map": self.check_in_map,
                "x_in_note": self.x_in_note,
                "x_out_note": self.x_out_note,
                "check_out_map": self.check_out_map,
                "employee_image": self.employee_image,
                "place_image": self.place_image,
                "user_in_image": self.user_in_image,
                "place_in_image": self.place_in_image,
                "user_out_image": self.user_out_image,
                "place_out_image": self.place_out_image,
            }]
        }

        try:
            success = self.websocket_client_id.send_message_to_client(
                self.websocket_client_id.client_id,
                message
            )
            if success:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': f"Message sent to {self.websocket_client_id.client_id}",
                        'type': 'success',
                        'sticky': False,
                    }
                }
            raise UserError("Delivery failed (no acknowledgement received)")
        except Exception as e:
            raise UserError(f"Delivery failed: {str(e)}")


    def _prepare_result_message(self, success_count, failed_clients):
        """Helper method to format the result message"""
        message_parts = []
        if success_count:
            message_parts.append(f"Sent to {success_count} client(s)")
        if failed_clients:
            if len(failed_clients) > 3:  # Don't show all if too many
                message_parts.append(f"failed for {len(failed_clients)} clients")
            else:
                message_parts.append(f"failed for: {', '.join(failed_clients)}")
        return "; ".join(message_parts) if message_parts else "No action taken"