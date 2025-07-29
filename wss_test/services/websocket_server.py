import asyncio
import websockets
import json
import uuid
import odoo
from odoo.api import Environment
from odoo.exceptions import AccessError, ValidationError
from odoo import fields
import logging
from typing import Dict
from datetime import timedelta
_logger = logging.getLogger(__name__)
ODOO_RC = '/opt/odoo16/odoo/conf/odoo.conf'
DB_NAME = 'odoo16dev'

# Define allowed models and their required/optional fields
ALLOWED_MODELS = {
    'wss.test': {
        'required': ['name', 'age'],
        'optional': ['description'],
        'field_types': {
            'name': str,
            'age': int,
        }
    },
    'test.api': {
        'required': ['name', 'test_integer'],
        'optional': ['description'],
        'field_types': {
            'name': str,
            'test_integer': int,
        }
    },
    'check.attendance': {
        'required': ['name'],
        'optional': ['check_out', 'check_in', 'employee_id'],
        'field_types': {
            'name': str,
            'check_in': str,
            'check_out': str,
            'employee_id': int,

        },
        'search_fields': ['name', 'employee_id', 'check_in', 'check_out'],
            'allowed_actions': ['create', 'read', 'get', 'get_sender_name','listen_attendance']
    },
    'mobile_app': {
        'required': ['name'],

        'field_types': {
            'name': str,

        },
        'search_fields': ['name'],
            'allowed_actions': ['create', 'read', 'get', 'get_sender_name','listen_attendance']
    }
}

class ClientManager:
    def __init__(self):
        self.clients = {}  # Format: {client_id: (websocket, path)}
        self.client_info = {}  # Additional client metadata
        self.registry = None  # Will hold Odoo registry reference

    def set_registry(self, registry):
        """Set the Odoo registry reference"""
        self.registry = registry

    async def add_client(self, websocket, path):
        """Add a new client connection"""
        client_id = str(uuid.uuid4())
        ip_address = websocket.remote_address[0] if websocket.remote_address else 'unknown'
        now = fields.Datetime.now()

        # Store connection information
        self.clients[client_id] = (websocket, path)
        self.client_info[client_id] = {
            'connected_at': now,
            'ip_address': ip_address,
            'path': path,
            'active_requests': 0
        }

        # Create record in Odoo database
        if self.registry:
            with self.registry.cursor() as cr:
                env = Environment(cr, odoo.SUPERUSER_ID, {})
                env['websocket.clients'].create({
                    'client_id': client_id,
                    'name': f"Client {client_id[:8]}",
                    'ip_address': ip_address,
                    'path': path,
                    'is_active': True,
                    'connected_at': now,
                    'last_activity': now
                })

        print(f"New client connected: {client_id} on path: {path}")
        return client_id

    async def remove_client(self, client_id):
        """Remove a client connection"""
        if client_id in self.clients:
            # Update Odoo database
            if self.registry:
                with self.registry.cursor() as cr:
                    env = Environment(cr, odoo.SUPERUSER_ID, {})
                    client = env['websocket.clients'].search([('client_id', '=', client_id)], limit=1)
                    if client:
                        client.write({
                            'is_active': False,
                            'disconnected_at': fields.Datetime.now()
                        })

            del self.clients[client_id]
            if client_id in self.client_info:
                del self.client_info[client_id]
            print(f"Client disconnected: {client_id}")

    async def update_client_activity(self, client_id):
        """Update client's last activity timestamp"""
        if client_id in self.client_info:
            self.client_info[client_id]['last_activity'] = fields.Datetime.now()
            if self.registry:
                with self.registry.cursor() as cr:
                    env = Environment(cr, odoo.SUPERUSER_ID, {})
                    client = env['websocket.clients'].search([('client_id', '=', client_id)], limit=1)
                    if client:
                        client.write({
                            'last_activity': fields.Datetime.now()
                        })

    async def post_to_client(self, client_id, message):
        """Post a message to a specific client"""
        if client_id in self.clients:
            websocket, _ = self.clients[client_id]
            try:
                await websocket.send(json.dumps(message))
                return True
            except Exception as e:
                print(f"Error posting to client {client_id}: {str(e)}")
                await self.remove_client(client_id)
        return False

client_manager = ClientManager()

def initialize_odoo():
    try:
        odoo.tools.config.parse_config(['-c', ODOO_RC])
        odoo.tools.config['load_language'] = False
        odoo.tools.config['without_demo'] = True
        odoo.tools.config['init'] = {}
        odoo.tools.config['update'] = {}
        odoo.cli.server.report_configuration()
        odoo.modules.registry.Registry.new(DB_NAME, force_demo=False, update_module=False)
        return odoo.registry(DB_NAME)
    except Exception as e:
        print(f"Failed to initialize Odoo: {str(e)}")
        raise

def validate_request_data(model, data):
    if model not in ALLOWED_MODELS:
        raise ValueError(f"Model '{model}' is not supported")

    model_config = ALLOWED_MODELS[model]
    validated_data = {}

    for field in model_config['required']:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
        if not isinstance(data[field], model_config['field_types'][field]):
            raise ValueError(f"Field '{field}' must be of type {model_config['field_types'][field].__name__}")
        validated_data[field] = data[field]

    for field in model_config['optional']:
        if field in data:
            if not isinstance(data[field], model_config['field_types'][field]):
                raise ValueError(f"Field '{field}' must be of type {model_config['field_types'][field].__name__}")
            validated_data[field] = data[field]

    return validated_data


async def handle_message(websocket, client_id, registry, message):
    try:
        data = json.loads(message)
        if data.get('sender') == 'odoo':
            # This is a message from Odoo, send acknowledgment
            ack = {
                'message_id': data.get('message_id'),
                'status': 'received',
                'timestamp': fields.Datetime.now().isoformat(),
                'client_id': client_id
            }
            await websocket.send(json.dumps(ack))
            return None  # Skip further processing for Odoo messages

        action = data.get('action')

        response_base = {
            'client_id': client_id,
            'request_id': data.get('request_id', str(uuid.uuid4()))
        }

        # Handle ping/register requests separately
        if action == 'ping':
            await client_manager.update_client_activity(client_id)
            return {
                **response_base,
                'status': 'success',
                'message': 'pong',
                'timestamp': fields.Datetime.now()
            }


        # if action == 'register':
        #     # Validate required fields
        #     if 'name' not in data:
        #         raise ValueError("Name is required for registration")
        #     if 'sender_id' not in data:
        #         raise ValueError("sender_id is required for registration")
        #     if 'client_id' not in data:
        #         data['client_id'] = str(uuid.uuid4())  # Generate new client_id if not provided
        #
        #     # Get or create client info
        #     if client_id not in client_manager.client_info:
        #         client_manager.client_info[client_id] = {}
        #
        #     # Update client information
        #     client_manager.client_info[client_id].update({
        #         'name': data['name'],
        #         'sender_id': data['sender_id'],
        #         'client_id': data['client_id'],
        #         'last_activity': fields.Datetime.now()
        #     })
        #
        #     # Update database record
        #     if client_manager.registry:
        #         with client_manager.registry.cursor() as cr:
        #             env = Environment(cr, odoo.SUPERUSER_ID, {})
        #             client = env['websocket.clients'].search([('client_id', '=', client_id)], limit=1)
        #             if client:
        #                 client.write({
        #                     'name': data['name'],
        #                     'sender_id': data['sender_id'],
        #                     'is_active': True,
        #                     'last_activity': fields.Datetime.now()
        #                 })
        #             else:
        #                 env['websocket.clients'].create({
        #                     'client_id': client_id,
        #                     'name': data['name'],
        #                     'sender_id': data['sender_id'],
        #                     'is_active': True,
        #                     'connected_at': fields.Datetime.now(),
        #                     'last_activity': fields.Datetime.now()
        #                 })
        #
        #
        #     return {
        #         **response_base,
        #         'status': 'success',
        #         'client_id': client_id,
        #         'message': 'Client registered successfully'
        #     }
        # if action == 'register':
        #     # Validate required fields
        #     if 'name' not in data:
        #         raise ValueError("Name is required for registration")
        #     if 'sender_id' not in data:
        #         raise ValueError("sender_id is required for registration")
        #     if 'client_id' not in data:
        #         data['client_id'] = str(uuid.uuid4())  # Generate new client_id if not provided
        #
        #     # Get or create client info
        #     if client_id not in client_manager.client_info:
        #         client_manager.client_info[client_id] = {}
        #
        #     # Update client information
        #     client_manager.client_info[client_id].update({
        #         'name': data['name'],
        #         'sender_id': data['sender_id'],
        #         'client_id': data['client_id'],
        #         'last_activity': fields.Datetime.now()
        #     })
        #
        #     # Update database record
        #     if client_manager.registry:
        #         with client_manager.registry.cursor() as cr:
        #             env = Environment(cr, odoo.SUPERUSER_ID, {})
        #
        #             # Handle websocket client record
        #             client = env['websocket.clients'].search([('client_id', '=', client_id)], limit=1)
        #             if client:
        #                 client.write({
        #                     'name': data['name'],
        #                     'sender_id': data['sender_id'],
        #                     'is_active': True,
        #                     'last_activity': fields.Datetime.now()
        #                 })
        #             else:
        #                 env['websocket.clients'].create({
        #                     'client_id': client_id,
        #                     'name': data['name'],
        #                     'sender_id': data['sender_id'],
        #                     'is_active': True,
        #                     'connected_at': fields.Datetime.now(),
        #                     'last_activity': fields.Datetime.now()
        #                 })
        #
        #             # Search for pending tracking.send records with related data
        #             pending_messages = env['tracking.send'].search([
        #                 ('sender_id', '=', data['sender_id']),
        #                 ('is_send', '=', False)
        #             ])
        #
        #             # Prepare pending assignments data
        #             pending_assignments = []
        #             for message in pending_messages:
        #                 pending_assignments.append({
        #                     'mobile_app_id': message.mobile_app_id.id,
        #                     'mobile_app_name': message.mobile_app_id.name,  # Assuming name field exists
        #                     'employee_id': message.employee_id.id,
        #                     'employee_name': message.employee_id.name,
        #                     'department_id': message.department_id.id if message.department_id else False,
        #                     'department_name': message.department_id.name if message.department_id else False,
        #                     'tracking_id': message.id
        #                 })
        #
        #             # Prepare response
        #             response_data = {
        #                 **response_base,
        #                 'status': 'success',
        #                 'client_id': client_id,
        #                 'message': 'Client registered successfully',
        #                 'pending_assignments': pending_assignments
        #             }
        #
        #     return response_data
        # if action == 'register':
        #     # Validate required fields
        #     if 'name' not in data:
        #         raise ValueError("Name is required for registration")
        #     if 'sender_id' not in data:
        #         raise ValueError("sender_id is required for registration")
        #     if 'client_id' not in data:
        #         data['client_id'] = str(uuid.uuid4())  # Generate new client_id if not provided
        #
        #     # Get or create client info
        #     if client_id not in client_manager.client_info:
        #         client_manager.client_info[client_id] = {}
        #
        #     # Update client information
        #     client_manager.client_info[client_id].update({
        #         'name': data['name'],
        #         'sender_id': data['sender_id'],
        #         'client_id': data['client_id'],
        #         'last_activity': fields.Datetime.now()
        #     })
        #
        #     # Update database record
        #     if client_manager.registry:
        #         with client_manager.registry.cursor() as cr:
        #             env = Environment(cr, odoo.SUPERUSER_ID, {})
        #
        #             # Handle websocket client record
        #             client = env['websocket.clients'].search([('client_id', '=', client_id)], limit=1)
        #             if client:
        #                 client.write({
        #                     'name': data['name'],
        #                     'sender_id': data['sender_id'],
        #                     'is_active': True,
        #                     'last_activity': fields.Datetime.now()
        #                 })
        #             else:
        #                 env['websocket.clients'].create({
        #                     'client_id': client_id,
        #                     'name': data['name'],
        #                     'sender_id': data['sender_id'],
        #                     'is_active': True,
        #                     'connected_at': fields.Datetime.now(),
        #                     'last_activity': fields.Datetime.now()
        #                 })
        #
        #             # Search for pending tracking.send records with related data
        #             pending_messages = env['tracking.send'].search([
        #                 ('sender_id', '=', data['sender_id']),
        #                 ('is_send', '=', False)
        #             ])
        #
        #             # Prepare pending assignments data
        #             pending_assignments = []
        #             mobile_apps_to_notify = set()  # Track unique mobile apps that need notification
        #
        #             for message in pending_messages:
        #                 pending_assignments.append({
        #                     'mobile_app_id': message.mobile_app_id.id,
        #                     'mobile_app_name': message.mobile_app_id.name,
        #                     'employee_id': message.employee_id.id,
        #                     'employee_name': message.employee_id.name,
        #                     'department_id': message.department_id.id if message.department_id else False,
        #                     'department_name': message.department_id.name if message.department_id else False,
        #                     'tracking_id': message.id
        #                 })
        #                 mobile_apps_to_notify.add(message.mobile_app_id.id)
        #
        #             # Find all active clients with the same sender_id
        #             same_sender_clients = env['websocket.clients'].search([
        #                 ('sender_id', '=', data['sender_id']),
        #                 ('is_active', '=', True),
        #                 ('client_id', '!=', client_id)  # Exclude the current client
        #             ])
        #
        #             # Trigger websocket notification for each relevant mobile app
        #             notification_results = []
        #             for app_id in mobile_apps_to_notify:
        #                 mobile_app = env['mobile_app'].browse(app_id)
        #                 try:
        #                     # Send to the current client
        #                     current_result = mobile_app.action_send_via_websocket(client_id=client_id)
        #
        #                     # Send to other clients with the same sender_id
        #                     other_results = []
        #                     for other_client in same_sender_clients:
        #                         try:
        #                             result = mobile_app.action_send_via_websocket(client_id=other_client.client_id)
        #                             other_results.append({
        #                                 'client_id': other_client.client_id,
        #                                 'status': 'success',
        #                                 'result': result
        #                             })
        #                         except Exception as e:
        #                             other_results.append({
        #                                 'client_id': other_client.client_id,
        #                                 'status': 'error',
        #                                 'error': str(e)
        #                             })
        #
        #                     notification_results.append({
        #                         'mobile_app_id': app_id,
        #                         'current_client_status': 'success',
        #                         'current_client_result': current_result,
        #                         'other_clients': other_results
        #                     })
        #                 except Exception as e:
        #                     notification_results.append({
        #                         'mobile_app_id': app_id,
        #                         'status': 'error',
        #                         'error': str(e)
        #                     })
        #
        #             # Prepare response
        #             response_data = {
        #                 **response_base,
        #                 'status': 'success',
        #                 'client_id': client_id,
        #                 'message': 'Client registered successfully',
        #                 'pending_assignments': pending_assignments,
        #                 'notifications_sent': {
        #                     'total_mobile_apps': len(mobile_apps_to_notify),
        #                     'total_clients_notified': 1 + len(same_sender_clients),
        #                     'current_client': {
        #                         'status': 'success',
        #                         'client_id': client_id
        #                     },
        #                     'other_clients': [{
        #                         'client_id': client.client_id,
        #                         'name': client.name
        #                     } for client in same_sender_clients],
        #                     'notification_details': notification_results
        #                 }
        #             }
        #
        #     return response_data
        if action == 'register':
            # [Previous validation and client setup code remains the same...]

            with client_manager.registry.cursor() as cr:
                env = Environment(cr, odoo.SUPERUSER_ID, {})

                # [Previous client registration code remains the same...]

                # Search for pending tracking.send records
                pending_messages = env['tracking.send'].search([
                    ('sender_id', '=', data['sender_id']),
                    ('is_send', '=', False)
                ])

                pending_assignments = []
                mobile_apps_to_notify = set()

                for message in pending_messages:
                    pending_assignments.append({
                        'mobile_app_id': message.mobile_app_id.id,
                        'mobile_app_name': message.mobile_app_id.name,
                        'employee_id': message.employee_id.id,
                        'employee_name': message.employee_id.name,
                        'department_id': message.department_id.id if message.department_id else False,
                        'department_name': message.department_id.name if message.department_id else False,
                        'tracking_id': message.id
                    })
                    mobile_apps_to_notify.add(message.mobile_app_id.id)

                # Find all active clients with same sender_id (including current one)
                target_clients = env['websocket.clients'].search([
                    ('sender_id', '=', data['sender_id']),
                    ('is_active', '=', True)
                ])

                notification_results = []
                messages_sent = 0

                for app_id in mobile_apps_to_notify:
                    mobile_app = env['mobile_app'].browse(app_id)
                    app_results = {
                        'mobile_app_id': app_id,
                        'clients': []
                    }
                    app_messages = [m for m in pending_assignments if m['mobile_app_id'] == app_id]
                    for client in target_clients:
                        try:
                            # Get the specific client's pending messages
                            client_messages = pending_messages.filtered(
                                lambda m: m.mobile_app_id.id == app_id
                            )

                            if client_messages:
                                # Format message data for this client
                                message_data = {
                                    'action': 'new_assignment',
                                    'data': {
                                        'assignments': [{
                                            'mobile_app_id': m.mobile_app_id.id,
                                            'tracking_id': m.id,
                                            # Include other relevant fields
                                        } for m in client_messages]
                                    }
                                }

                                # Send directly via client_manager
                                # client_manager.send_message(
                                #     client_id=client.client_id,
                                #     message=message_data
                                # )

                                app_results['clients'].append({
                                    'client_id': client.client_id,
                                    'status': 'success',
                                    'messages_sent': len(client_messages)
                                })
                                messages_sent += len(client_messages)

                        except Exception as e:
                            app_results['clients'].append({
                                'client_id': client.client_id,
                                'status': 'error',
                                'error': str(e)
                            })

                    notification_results.append(app_results)

                # Prepare response
                response_data = {
                    **response_base,
                    'status': 'success',
                    'client_id': client_id,
                    'message': 'Client registered successfully',
                    'pending_assignments': pending_assignments,
                    'notifications': {
                        'total_mobile_apps': len(mobile_apps_to_notify),
                        'total_clients': len(target_clients),
                        'total_messages_sent': messages_sent,
                        'details': notification_results
                    }
                }

            return response_data
        # For other actions, require model
        model = data.get('model')
        if not model:
            raise ValueError("Model name is required")

        with registry.cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})

            if model not in env:
                raise ValueError(f"Model '{model}' does not exist in database")

            if action == 'create':
                validated_data = validate_request_data(model, data)

                if not env[model].check_access_rights('create', raise_exception=False):
                    raise AccessError(f"No create permissions for model {model}")

                record = env[model].create(validated_data)
                return {
                    **response_base,
                    'status': 'success',
                    'message': 'Record created successfully',
                    'id': record.id
                }

            elif action == 'read':
                record_id = data.get('id')
                if not record_id:
                    raise ValueError("Record ID is required for read operation")

                if not env[model].check_access_rights('read', raise_exception=False):
                    raise AccessError(f"No read permissions for model {model}")

                record = env[model].browse(record_id)
                if not record.exists():
                    raise ValueError(f"Record with ID {record_id} not found")

                return {
                    **response_base,
                    'status': 'success',
                    'data': record.read()[0]
                }


            elif action == 'get':
                if not env[model].check_access_rights('read', raise_exception=False):
                    raise AccessError(f"No read permissions for model {model}")

                record_id = data.get('id')  # Get specific record ID if provided
                search_params = data.get('params', {})
                domain = []

                # Case 1: Fetch specific record by ID (new functionality)
                if record_id:
                    if not isinstance(record_id, int):
                        raise ValueError("Record ID must be an integer")

                    record = env[model].browse(record_id)
                    if not record.exists():
                        raise ValueError(f"Record with ID {record_id} not found")

                    # Build response for single record
                    record_data = {
                        'id': record.id,
                        'name': record.name,
                    }

                    # Add model-specific fields
                    if model == 'check.attendance':
                        record_data.update({
                            'employee_id': record.employee_id.id if record.employee_id else None,
                            'check_in': record.check_in.isoformat() if record.check_in else None,
                            'check_out': record.check_out.isoformat() if record.check_out else None,
                        })
                    elif model == 'mobile_app':
                        record_data.update({
                            'description': record.description if hasattr(record, 'description') else None,
                        })

                    return {
                        **response_base,
                        'status': 'success',
                        'data': record_data,  # Single record (not a list)
                        'count': 1
                    }

                # Case 2: Original search functionality (unchanged)
                if model in ALLOWED_MODELS and 'search_fields' in ALLOWED_MODELS[model]:
                    allowed_fields = ALLOWED_MODELS[model]['search_fields']
                    for field, value in search_params.items():
                        if field not in allowed_fields:
                            raise ValueError(f"Field '{field}' is not allowed for searching")

                        if field in ['check_in', 'check_out']:
                            if isinstance(value, str) and len(value) == 10:
                                domain.append((field, '>=', f"{value} 00:00:00"))
                                domain.append((field, '<=', f"{value} 23:59:59"))
                            else:
                                domain.append((field, '=', value))
                        else:
                            domain.append((field, '=', value))

                records = env[model].search(domain)

                result = []
                for record in records:
                    record_data = {
                        'id': record.id,
                        'name': record.name,
                    }
                    if model == 'check.attendance':
                        record_data.update({
                            'employee_id': record.employee_id.id if record.employee_id else None,
                            'check_in': record.check_in.isoformat() if record.check_in else None,
                            'check_out': record.check_out.isoformat() if record.check_out else None,
                        })
                    elif model == 'mobile_app':
                        record_data.update({
                            'description': record.description if hasattr(record, 'description') else None,
                        })
                    result.append(record_data)

                return {
                    **response_base,
                    'status': 'success',
                    'data': result,
                    'count': len(result)
                }
            elif action == 'get_sender_name':
                sender_id = data.get('sender_id')
                if not sender_id:
                    raise ValueError("sender_id is required")

                with registry.cursor() as cr:
                    env = Environment(cr, odoo.SUPERUSER_ID, {})

                    if not env['check.attendance'].check_access_rights('read', raise_exception=False):
                        raise AccessError("No read permissions for check.attendance model")

                    record = env['check.attendance'].browse(sender_id)
                    if not record.exists():
                        raise ValueError(f"No attendance record found with ID {sender_id}")

                    return {
                        **response_base,
                        'status': 'success',
                        'sender_name': record.name,
                        'sender_id': sender_id
                    }


            elif action == 'listen_attendance':
                # This is a special action that just acknowledges the subscription
                # The actual data will be sent via send_message_to_client
                return {
                    **response_base,
                    'status': 'success',
                    'message': 'Now listening for attendance updates'
                }

            else:
                raise ValueError(f"Unsupported action: {action}")

    except json.JSONDecodeError as e:
        return {
            'status': 'error',
            'message': f'Invalid JSON: {str(e)}',
            'client_id': client_id
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'client_id': client_id
        }


async def handle_odoo_message(websocket, message):
    """Handle messages coming from Odoo"""
    try:
        data = json.loads(message)
        target_client = data.get('target_client')
        payload = data.get('payload')

        if target_client in client_manager.clients:
            # Forward to target client
            await client_manager.post_to_client(target_client, payload)

            # Send simple acknowledgment
            await websocket.send("ACK")
            return True
        return False
    except Exception as e:
        print(f"Error handling Odoo message: {str(e)}")
        return False


async def handler(websocket, path=None):
    """WebSocket connection handler"""
    client_id = None
    try:
        # Initialize Odoo
        registry = initialize_odoo()
        client_manager.set_registry(registry)

        # First message must identify connection type
        first_message = await websocket.recv()
        msg_data = json.loads(first_message)

        # Handle Odoo system messages
        if msg_data.get('sender') == 'odoo':
            client_id = msg_data.get('target_client')
            if not client_id:
                await websocket.send(json.dumps({
                    'status': 'error',
                    'message': 'Target client ID required'
                }))
                return

            if client_id in client_manager.clients:
                await client_manager.clients[client_id].send(json.dumps(msg_data.get('payload')))
                await websocket.send(json.dumps({
                    'status': 'success',
                    'message': 'Message forwarded'
                }))
            else:
                await websocket.send(json.dumps({
                    'status': 'error',
                    'message': 'Target client not connected'
                }))
            return

        # Handle client registration
        elif msg_data.get('action') == 'register':
            if 'sender_id' not in msg_data:
                raise ValueError("sender_id is required for registration")

            client_id = msg_data.get('client_id', str(uuid.uuid4()))

            with registry.cursor() as cr:
                env = Environment(cr, odoo.SUPERUSER_ID, {})
                client = env['websocket.clients'].search([
                    ('client_id', '=', client_id)
                ], limit=1)

                vals = {
                    'sender_id': msg_data['sender_id'],
                    'is_active': True,
                    'last_activity': fields.Datetime.now()
                }
                if not client:
                    vals.update({
                        'client_id': client_id,
                        'name': msg_data.get('name', f"Client {client_id[:8]}"),
                        'connected_at': fields.Datetime.now()
                    })
                    client = env['websocket.clients'].create(vals)
                else:
                    client.write(vals)

            client_manager.clients[client_id] = websocket

            # Send responses
            await websocket.send(json.dumps({
                'status': 'success',
                'client_id': client_id,
                'message': 'Registration successful'
            }))

            await websocket.send(json.dumps({
                'status': 'connected',
                'client_id': client_id,
                'supported_models': list(ALLOWED_MODELS.keys())
            }))

            # Handle subsequent messages
            async for message in websocket:
                await client_manager.update_client_activity(client_id)
                try:
                    response = await handle_message(websocket, client_id, registry, message)
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': 'Invalid JSON format'
                    }))

        else:
            raise ValueError("First message must be registration or from Odoo")

    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Connection error: {str(e)}")
    finally:
        if client_id:
            with registry.cursor() as cr:
                env = Environment(cr, odoo.SUPERUSER_ID, {})
                env['websocket.clients'].search([
                    ('client_id', '=', client_id)
                ]).write({
                    'is_active': False,
                    'disconnected_at': fields.Datetime.now()
                })
            if client_id in client_manager.clients:
                del client_manager.clients[client_id]
async def main():
    # Start WebSocket server
    async with websockets.serve(
            handler,
            "0.0.0.0",
            8765,
            ping_interval=20,
            ping_timeout=20,
            max_size=2**20
    ):
        print(f"Server running on ws://0.0.0.0:8765 for {DB_NAME}")
        print(f"Supported models: {', '.join(ALLOWED_MODELS.keys())}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())