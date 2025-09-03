import asyncio
import websockets
import json
import uuid
import odoo
from odoo.api import Environment
from odoo import fields
import logging

logger = logging.getLogger(__name__)  # Fixed: changed name_ to __name__

ODOO_RC = '/opt/odoo16/odoo/conf/odoo.conf'
DB_NAME = 'websocket_16'
WS_HOST = "0.0.0.0"
WS_PORT = 2083

ALLOWED_MODELS = {
    'mobile_app': {
        'allowed_actions': ['create', 'read', 'update', 'delete'],
        'm2m_fields': ['employees_id'],
    },
    'project.task': {
        'allowed_actions': ['create', 'read', 'update']
    },
    'wss_test': {
        'allowed_actions': ['read', 'update']
    }
}


def get_client_model_name(cr):
    env = Environment(cr, odoo.SUPERUSER_ID, {})
    if 'wss_test' in env:
        return 'wss_test'
    if 'websocket.clients' in env:
        return 'websocket.clients'
    return 'wss_test'


class ClientManager:

    def __init__(self):  # Fixed: changed _init_ to __init__
        self.clients = {}
        self.registry = None

    def set_registry(self, registry):
        self.registry = registry

    async def add_client(self, websocket):
        client_id = str(uuid.uuid4())
        ip_address = websocket.remote_address[
            0] if websocket.remote_address else 'unknown'
        self.clients[client_id] = {
            'websocket': websocket, 'ip_address': ip_address
        }

        if self.registry:
            try:
                with self.registry.cursor() as cr:
                    env = Environment(cr, odoo.SUPERUSER_ID, {})
                    client_model = get_client_model_name(cr)
                    if client_model in env:
                        env[client_model].create({
                            'client_id': client_id,
                            'name': f'Client {client_id[:8]}',
                            'is_active': True,
                            'connected_at': fields.Datetime.now(),
                            'last_activity': fields.Datetime.now(),
                            'ip_address': ip_address,
                        })
            except Exception:
                logger.exception("Failed to create customer record in DB")  # Fixed: changed _logger to logger

        logger.info("Client added: %s (ip=%s)", client_id, ip_address)  # Fixed: changed _logger to logger
        return client_id

    async def register_client(self, client_id, sender_id):
        if not self.registry or client_id not in self.clients:
            return None
        try:
            with self.registry.cursor() as cr:
                env = Environment(cr, odoo.SUPERUSER_ID, {})
                client_model = get_client_model_name(cr)
                if client_model not in env:
                    return None
                rec = env[client_model].search([('client_id', '=', client_id)],
                                               limit=1)
                if rec:
                    rec.write({
                        'sender_id': sender_id,
                        'is_active': True,
                        'last_activity': fields.Datetime.now()
                    })
                    emp = env['hr.employee'].search(
                        [('sender_id', '=', sender_id)], limit=1)
                    if emp:
                        try:
                            rec.write({'employee_id': emp.id})
                        except Exception:
                            pass
                        return {'id': emp.id, 'name': emp.name}
        except Exception:
            logger.exception("Error in register_client")  # Fixed: changed _logger to logger
        return None

    async def remove_client(self, client_id):
        try:
            if client_id in self.clients:
                try:
                    ws = self.clients[client_id].get('websocket')
                    if ws:
                        await ws.close()
                except Exception:
                    pass
                del self.clients[client_id]
                logger.info("Removed client: %s", client_id)  # Fixed: changed _logger to logger
        except Exception:
            logger.exception("Error removing client from memory")  # Fixed: changed _logger to logger

        if self.registry:
            try:
                with self.registry.cursor() as cr:
                    env = Environment(cr, odoo.SUPERUSER_ID, {})
                    client_model = get_client_model_name(cr)
                    if client_model in env:
                        rec = env[client_model].search(
                            [('client_id', '=', client_id)], limit=1)
                        if rec:
                            rec.write({
                                'is_active': False,
                                'last_activity': fields.Datetime.now()
                            })
            except Exception:
                logger.exception("Error updating client inactive in DB")  # Fixed: changed _logger to logger

    async def send_to_sender_ids(self, sender_ids, payload, task_id=None):
        not_delivered = []
        delivered_map = {}
        if not self.registry:
            return list(sender_ids)
        try:
            with self.registry.cursor() as cr:
                env = Environment(cr, odoo.SUPERUSER_ID, {})
                client_model = get_client_model_name(cr)
                client_recs = env[client_model].search(
                    [('sender_id', 'in', sender_ids), ('is_active', '=', True)])
                sender_map = {}
                for r in client_recs:
                    sender_map.setdefault(r.sender_id, []).append(r)

                for s in sender_ids:
                    recs = sender_map.get(s, [])
                    delivered = False
                    if recs:
                        for r in recs:
                            cid = r.client_id
                            if cid in self.clients:
                                ws = self.clients[cid]['websocket']
                                try:
                                    await ws.send(json.dumps(payload))
                                    delivered = True
                                    break
                                except Exception:
                                    pass
                    if not delivered:
                        not_delivered.append(s)
                    delivered_map[s] = delivered

                if task_id:
                    for s in sender_ids:
                        is_sent = bool(delivered_map.get(s, False))
                        status = 'delivered' if is_sent else 'not_delivered'
                        env['mobile_app.tracking'].create({
                            'task_id': task_id,
                            'sender_id': s,
                            'status': status,
                            'is_send': is_sent
                        })
        except Exception:
            logger.exception("Error in send_to_sender_ids")  # Fixed: changed _logger to logger
            return list(sender_ids)
        return not_delivered


client_manager = ClientManager()


def initialize_odoo():
    odoo.tools.config.parse_config(['-c', ODOO_RC])
    odoo.modules.registry.Registry.new(DB_NAME)
    return odoo.registry(DB_NAME)


def _is_action_allowed(model, action):
    mdl = ALLOWED_MODELS.get(model)
    return mdl and action in mdl.get('allowed_actions', [])


async def handle_client_message(websocket, client_id, registry, message):
    try:
        payload = json.loads(message)
    except json.JSONDecodeError:
        return {
            'status': 'error', 'message': 'Invalid JSON', 'client_id': client_id
        }

    action = (payload.get('action') or '').lower()
    if action == 'ping':
        return {'status': 'success', 'message': 'pong', 'client_id': client_id}

    if action == 'register':
        sender_id = payload.get('sender_id')
        if not sender_id:
            return {
                'status': 'error', 'message': 'sender_id required',
                'client_id': client_id
            }
        emp_data = await client_manager.register_client(client_id, sender_id)
        if emp_data:
            return {
                'status': 'success',
                'message': 'registered and linked to employee',
                'employee': emp_data,
                'client_id': client_id
            }
        return {
            'status': 'success', 'message': 'registered', 'client_id': client_id
        }

    model = payload.get('model')
    if not model or not _is_action_allowed(model, action):
        return {
            'status': 'error',
            'message': f'action {action} not allowed for model {model}',
            'client_id': client_id
        }

    try:
        with registry.cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})

            if model == 'mobile_app' and action == 'create':
                rec = payload.get('data', [])[0]
                name = rec.get('name')
                employees_id = rec.get('employees_id', [])

                valid_emp_ids = []
                sender_ids = []
                for eid in employees_id:
                    emp = env['hr.employee'].browse(int(eid))
                    if emp.exists():
                        valid_emp_ids.append(emp.id)
                        if emp.sender_id:
                            sender_ids.append(emp.sender_id)

                task = env['mobile_app'].create({
                    'name': name,
                    'employees_id': [(6, 0, valid_emp_ids)]
                })

                outgoing = {
                    "action": "get",
                    "model": "mobile_app",
                    "data": [{
                        "name": task.name,
                        "employees_id": valid_emp_ids
                    }]
                }

                sender_ids = list(dict.fromkeys(sender_ids))
                not_delivered = await client_manager.send_to_sender_ids(
                    sender_ids, outgoing, task_id=task.id)
                return {
                    'status': 'success',
                    'message': 'task created and notifications processed',
                    'task_id': task.id,
                    'not_delivered': not_delivered
                }

    except Exception:
        logger.exception("Error processing request")  # Fixed: changed _logger to logger
        return {
            'status': 'error', 'message': 'internal server error',
            'client_id': client_id
        }


async def websocket_handler(websocket):
    client_id = None
    registry = None
    try:
        registry = initialize_odoo()
        client_manager.set_registry(registry)
        client_id = await client_manager.add_client(websocket)

        await websocket.send(json.dumps({
            'status': 'connected',
            'client_id': client_id,
            'message': 'Connected to WebSocket server'
        }))

        async for message in websocket:
            resp = await handle_client_message(websocket, client_id, registry,
                                               message)
            await websocket.send(json.dumps(resp))
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception:
        logger.exception("General websocket handler error")  # Fixed: changed _logger to logger
    finally:
        if client_id:
            await client_manager.remove_client(client_id)


async def main():
    # تشغيل بدون SSL
    async with websockets.serve(websocket_handler, WS_HOST, WS_PORT):
        logger.info("WebSocket server running on ws://%s:%s", WS_HOST, WS_PORT)  # Fixed: changed _logger to logger
        await asyncio.Future()


if __name__ == "__main__":  # Fixed: changed _name_ to __name__
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")  # Fixed: changed _logger to logger