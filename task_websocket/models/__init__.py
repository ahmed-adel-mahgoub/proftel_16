# -*- coding: utf-8 -*-

from . import models
from . import websocket_server

def _start_websocket_server(cr, registry):
    """Start the websocket server when module is loaded"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['websocket.server'].start_server()