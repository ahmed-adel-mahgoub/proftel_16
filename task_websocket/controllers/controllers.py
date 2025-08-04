from odoo import http
from odoo.http import request

class WebsocketController(http.Controller):
    @http.route('/task_websocket/start', type='http', auth='public')
    def start_websocket(self):
        """Initialize the websocket server"""
        request.env['websocket.server'].start_server()
        return "Websocket server started on ws://0.0.0.0:8766"