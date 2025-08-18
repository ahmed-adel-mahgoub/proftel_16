# -*- coding: utf-8 -*-

from . import models
from . import websocket_server

from odoo import api, SUPERUSER_ID

def start_websocket_server(cr, registry):
    try:
        env = api.Environment(cr, SUPERUSER_ID, {})
        if 'websocket.server' in env:
            servers = env['websocket.server'].search([])
            if servers:
                servers.start_server()
    except Exception as e:
        _logger.error("Failed to start WebSocket server: %s", e)
        raise
def post_init_hook(cr, registry):
    """Called after module installation"""
    start_websocket_server(cr, registry)