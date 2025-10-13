from odoo import http
from odoo.http import request, Response
import json
from datetime import datetime


class UserRulesEndpoint(http.Controller):

    # GET endpoint - Read user rules
    @http.route('/api/get/user-rules', auth='public', type='http', methods=['GET'],
                csrf=False)
    def get_user_rules(self, **kwargs):
        try:
            # Use sudo to bypass security rules
            rules = request.env['user.rules'].sudo().search([])

            result = []
            for rule in rules:
                result.append({
                    'id': rule.id,
                    'name': rule.name,
                    'company_ids': rule.company_ids.ids,
                    'department_ids': rule.department_ids.ids,
                    'employee_ids': rule.employee_ids.ids,
                    'rules_id': rule.rules_id.ids,
                    'app_module_id': rule.app_module_id.ids,
                    'wan_ip_id': rule.wan_ip_id.id if rule.wan_ip_id else False
                })

            return Response(
                json.dumps({
                    'status': 'success',
                    'data': result,
                    'message': 'User rules retrieved successfully'
                }),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500
            )

    # GET single record endpoint
    @http.route('/api/get/user-rules/<int:rule_id>', auth='public', type='http',
                methods=['GET'], csrf=False)
    def get_single_user_rule(self, rule_id, **kwargs):
        try:
            rule = request.env['user.rules'].sudo().browse(rule_id)

            if not rule.exists():
                return Response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Rule not found'
                    }),
                    content_type='application/json',
                    status=404
                )

            result = {
                'id': rule.id,
                'name': rule.name,
                'company_ids': rule.company_ids.ids,
                'department_ids': rule.department_ids.ids,
                'employee_ids': rule.employee_ids.ids,
                'rules_id': rule.rules_id.ids,
                'app_module_id': rule.app_module_id.ids,
                'wan_ip_id': rule.wan_ip_id.id if rule.wan_ip_id else False
            }

            return Response(
                json.dumps({
                    'status': 'success',
                    'data': result,
                    'message': 'User rule retrieved successfully'
                }),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500
            )

    # POST endpoint - Create new user rule
    @http.route('/api/post/user-rules', auth='public', type='http',
                methods=['POST'], csrf=False)
    def create_user_rule_http(self, **kwargs):
        try:
            import json
            raw_data = request.httprequest.data
            data = json.loads(raw_data)

            # Helper function to format Many2many fields
            def format_many2many(field_data):
                if field_data is None:
                    return [(6, 0, [])]
                elif isinstance(field_data, list) and field_data and isinstance(
                        field_data[0], list):
                    # Already in correct format: [[6, 0, [1, 2, 3]]]
                    return field_data
                elif isinstance(field_data, list):
                    # Simple list format: [1, 2, 3] -> convert to [(6, 0, [1, 2, 3])]
                    return [(6, 0, field_data)]
                elif isinstance(field_data, int):
                    # Single ID: 2 -> convert to [(6, 0, [2])]
                    return [(6, 0, [field_data])]
                else:
                    # Empty or invalid
                    return [(6, 0, [])]

            # Validate required fields
            if not data.get('name'):
                return Response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Name field is required'
                    }),
                    content_type='application/json',
                    status=400
                )

            # Validate that company_ids is provided and not empty
            if 'company_ids' not in data:
                return Response(
                    json.dumps({
                        'status': 'error',
                        'message': 'company_ids field is required'
                    }),
                    content_type='application/json',
                    status=400
                )

            company_ids = data.get('company_ids')
            if not company_ids:
                return Response(
                    json.dumps({
                        'status': 'error',
                        'message': 'company_ids cannot be empty'
                    }),
                    content_type='application/json',
                    status=400
                )

            # Create record with sudo
            new_rule = request.env['user.rules'].sudo().create({
                'name': data.get('name'),
                'company_ids': format_many2many(data.get('company_ids')),
                'department_ids': format_many2many(
                    data.get('department_ids', [])),
                'employee_ids': format_many2many(data.get('employee_ids', [])),
                'rules_id': format_many2many(data.get('rules_id', [])),
                'app_module_id': format_many2many(
                    data.get('app_module_id', [])),
                'wan_ip_id': data.get('wan_ip_id', False)
            })

            return Response(
                json.dumps({
                    'status': 'success',
                    'data': {
                        'id': new_rule.id,
                        'name': new_rule.name,
                        'company_ids': new_rule.company_ids.ids
                    },
                    'message': 'User rule created successfully'
                }),
                content_type='application/json',
                status=201
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500
            )

    import json

    # PUT endpoint - Update user rule
    @http.route('/api/put/user-rules/<int:rule_id>', auth='public', type='http',
                methods=['PUT'], csrf=False)
    def update_user_rule_http(self, rule_id, **kwargs):
        try:
            # Parse JSON data from request body
            raw_data = request.httprequest.data
            data = json.loads(raw_data)

            rule = request.env['user.rules'].sudo().browse(rule_id)

            if not rule.exists():
                return Response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Rule not found'
                    }),
                    content_type='application/json',
                    status=404
                )

            update_data = {}
            if 'name' in data:
                update_data['name'] = data['name']
            if 'company_ids' in data:
                update_data['company_ids'] = [(6, 0, data['company_ids'])]
            if 'department_ids' in data:
                update_data['department_ids'] = [(6, 0, data['department_ids'])]
            if 'employee_ids' in data:
                update_data['employee_ids'] = [(6, 0, data['employee_ids'])]
            if 'rules_id' in data:
                update_data['rules_id'] = [(6, 0, data['rules_id'])]
            if 'app_module_id' in data:
                update_data['app_module_id'] = [(6, 0, data['app_module_id'])]
            if 'wan_ip_id' in data:
                update_data['wan_ip_id'] = data['wan_ip_id']

            rule.write(update_data)

            return Response(
                json.dumps({
                    'status': 'success',
                    'message': 'User rule updated successfully',
                    'data': {
                        'id': rule.id,
                        'name': rule.name
                    }
                }),
                content_type='application/json',
                status=200
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e)
                }),
                content_type='application/json',
                status=500
            )

    # DELETE endpoint - Delete user rule
    @http.route('/api/delete/user-rules/<int:rule_id>', auth='public', type='json',
                methods=['DELETE'], csrf=False)
    def delete_user_rule(self, rule_id, **kwargs):
        try:
            rule = request.env['user.rules'].sudo().browse(rule_id)

            if not rule.exists():
                return {
                    'status': 'error',
                    'message': 'Rule not found'
                }

            rule_name = rule.name
            rule.unlink()

            return {
                'status': 'success',
                'message': f'User rule "{rule_name}" deleted successfully'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    @http.route('/api/create_user', type='json', auth='public', methods=['POST'],
                csrf=False)
    def create_user(self, **post):
        """Public endpoint to create user"""
        try:
            data = json.loads(request.httprequest.data.decode())
            user_name = data.get('user_name')
            password = data.get('password')

            if not user_name or not password:
                return {"error": "user_name and password are required."}

            # Call the action
            record = request.env['user.data'].sudo().create({
                'user_name': user_name,
                'password': password,
            })
            user = record.sudo().action_create_user()

            return {"success": True, "user_id": user.id, "login": user.login}
        except Exception as e:
            return {"error": str(e)}