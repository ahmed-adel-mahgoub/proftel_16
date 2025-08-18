from odoo import http
from odoo.http import request

class WebsocketController(http.Controller):
    @http.route('/task_websocket/start', type='http', auth='public')
    def start_websocket(self):
        """Initialize the websocket server"""
        request.env['websocket.server'].start_server()
        return "Websocket server started on ws://0.0.0.0:8766"

    @http.route('/api/create_project', type='json', auth='public',
                methods=['POST'], csrf=False)
    def create_project(self, **kwargs):
        data = request.jsonrequest
        try:
            project = request.env['project.project'].sudo().create({
                'name': data.get('name'),
                'description': data.get('description', ''),
            })
            return {
                'status': 'success',
                'project_id': project.id,
                'message': 'Project created successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/create_task', type='json', auth='public', methods=['POST'],
                csrf=False)
    def create_task(self, **kwargs):
        data = request.jsonrequest
        try:
            # Get employee IDs from sender_ids
            sender_ids = data.get('assignees', [])
            employees = request.env['hr.employee'].sudo().search(
                [('sender_id', 'in', sender_ids)])

            task = request.env['project.task'].sudo().create({
                'name': data.get('name'),
                'description': data.get('description', ''),
                'project_id': data.get('project_id'),
                'member_ids': [(6, 0, employees.ids)],
            })

            # Notify assigned employees via websocket
            websocket_server = request.env['websocket.server'].sudo().search([],
                                                                             limit=1)
            if websocket_server:
                websocket_server.notify_task_update(task, action='create')

            return {
                'status': 'success',
                'task_id': task.id,
                'message': 'Task created and assigned successfully'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }