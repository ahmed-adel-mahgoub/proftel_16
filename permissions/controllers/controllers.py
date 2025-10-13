from odoo import http
from odoo.http import request, Response
import json
import logging
from datetime import datetime, date

_logger = logging.getLogger(__name__)


class RulesController(http.Controller):

    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)

    def _prepare_rule_data(self, rule):
        """Prepare rule data for JSON serialization"""
        if not rule:
            return {}

        # Read the rule and convert datetime fields
        rule_data = rule.read()[0]

        # Convert all fields to JSON serializable format
        serializable_data = {}
        for key, value in rule_data.items():
            if isinstance(value, (datetime, date)):
                serializable_data[key] = value.isoformat()
            elif isinstance(value, (list, tuple)) and value and isinstance(
                    value[0], (datetime, date)):
                serializable_data[key] = [
                    v.isoformat() if isinstance(v, (datetime, date)) else v for
                    v in value]
            else:
                serializable_data[key] = value

        return serializable_data

    @http.route('/api/post/rules', auth='public', type='http', methods=['POST'],
                csrf=False)
    def create_rule(self, **kwargs):
        """
        POST endpoint to create a new rule (Public access)
        """
        try:
            # Extract data from request
            data = json.loads(
                request.httprequest.data) if request.httprequest.data else kwargs

            # Prepare rule data
            rule_data = {
                'name': data.get('name'),
                'http_read': data.get('http_read', False),
                'http_write': data.get('http_write', False),
                'http_update': data.get('http_update', False),
                'http_delete': data.get('http_delete', False),
                'http_select_all': data.get('http_select_all', False),
                'ws_read': data.get('ws_read', False),
                'ws_write': data.get('ws_write', False),
                'ws_update': data.get('ws_update', False),
                'ws_delete': data.get('ws_delete', False),
                'ws_select_all': data.get('ws_select_all', False),
            }

            # Create the rule using sudo()
            rule = request.env['rules'].sudo().create(rule_data)

            # Prepare response data
            response_data = self._prepare_rule_data(rule)

            # Return success response
            return Response(
                json.dumps({
                    'success': True,
                    'message': 'Rule created successfully',
                    'rule_id': rule.id,
                    'data': response_data
                }, default=self._json_serial),
                status=201,
                mimetype='application/json'
            )

        except Exception as e:
            _logger.error(f"Error creating rule: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                status=400,
                mimetype='application/json'
            )

    @http.route('/api/get/rules/<int:rule_id>', auth='public', type='http',
                methods=['GET'], csrf=False)
    def read_rule(self, rule_id, **kwargs):
        """
        GET endpoint to read a specific rule (Public access)
        """
        try:
            # Find the rule using sudo()
            rule = request.env['rules'].sudo().browse(rule_id)
            if not rule.exists():
                return Response(
                    json.dumps({'error': 'Rule not found'}),
                    status=404,
                    mimetype='application/json'
                )

            # Prepare response data
            response_data = self._prepare_rule_data(rule)

            # Return rule data
            return Response(
                json.dumps({
                    'success': True,
                    'data': response_data
                }, default=self._json_serial),
                status=200,
                mimetype='application/json'
            )

        except Exception as e:
            _logger.error(f"Error reading rule: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                status=400,
                mimetype='application/json'
            )

    @http.route('/api/put/rules/<int:rule_id>', auth='public', type='http',
                methods=['PUT'], csrf=False)
    def update_rule(self, rule_id, **kwargs):
        """
        PUT endpoint to update a specific rule (Public access)
        """
        try:
            # Find the rule using sudo()
            rule = request.env['rules'].sudo().browse(rule_id)
            if not rule.exists():
                return Response(
                    json.dumps({'error': 'Rule not found'}),
                    status=404,
                    mimetype='application/json'
                )

            # Extract data from request
            data = json.loads(
                request.httprequest.data) if request.httprequest.data else kwargs

            # Prepare update data
            update_data = {}
            fields_to_update = [
                'name', 'http_read', 'http_write', 'http_update', 'http_delete',
                'http_select_all', 'ws_read', 'ws_write', 'ws_update',
                'ws_delete', 'ws_select_all'
            ]

            for field in fields_to_update:
                if field in data:
                    update_data[field] = data[field]

            # Update the rule using sudo()
            rule.sudo().write(update_data)

            # Prepare response data
            response_data = self._prepare_rule_data(rule)

            # Return success response
            return Response(
                json.dumps({
                    'success': True,
                    'message': 'Rule updated successfully',
                    'rule_id': rule.id,
                    'data': response_data
                }, default=self._json_serial),
                status=200,
                mimetype='application/json'
            )

        except Exception as e:
            _logger.error(f"Error updating rule: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                status=400,
                mimetype='application/json'
            )

    @http.route('/api/get/all/rules', auth='public', type='http', methods=['GET'],
                csrf=False)
    def read_all_rules(self, **kwargs):
        """
        GET endpoint to read all rules (Public access)
        """
        try:
            # Get all rules using sudo()
            rules = request.env['rules'].sudo().search([])

            # Prepare rules data for JSON serialization
            rules_data = []
            for rule in rules:
                rule_data = self._prepare_rule_data(rule)
                rules_data.append(rule_data)

            # Return rules data
            return Response(
                json.dumps({
                    'success': True,
                    'count': len(rules_data),
                    'data': rules_data
                }, default=self._json_serial),
                status=200,
                mimetype='application/json'
            )

        except Exception as e:
            _logger.error(f"Error reading rules: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                status=400,
                mimetype='application/json'
            )

    @http.route('/api/delete/rules/<int:rule_id>', auth='public', type='http',
                methods=['DELETE'], csrf=False)
    def delete_rule(self, rule_id, **kwargs):
        """
        DELETE endpoint to delete a specific rule (Public access)
        """
        try:
            # Find the rule using sudo()
            rule = request.env['rules'].sudo().browse(rule_id)
            if not rule.exists():
                return Response(
                    json.dumps({'error': 'Rule not found'}),
                    status=404,
                    mimetype='application/json'
                )

            # Delete the rule using sudo()
            rule.sudo().unlink()

            # Return success response
            return Response(
                json.dumps({
                    'success': True,
                    'message': 'Rule deleted successfully',
                    'rule_id': rule_id
                }),
                status=200,
                mimetype='application/json'
            )

        except Exception as e:
            _logger.error(f"Error deleting rule: {str(e)}")
            return Response(
                json.dumps({'error': str(e)}),
                status=400,
                mimetype='application/json'
            )
# =========================================================
    # GET all zones
    # =========================================================
    @http.route('/api/zones/get_all', type='http', auth='public', methods=['GET'], csrf=False)
    def get_all_zones(self, **kwargs):
        zones = request.env['zones'].sudo().search([])
        data = [{
            'id': z.id,
            'name': z.name,
            'description': z.description,
            'note': z.note,
            'regions': z.regions,
            'countries': z.countries,
            'cities': z.cities,
            'companies': [{'id': c.id, 'name': c.name} for c in z.company_ids],
        } for z in zones]

        return http.Response(json.dumps(data), content_type='application/json')

    # =========================================================
    # GET single zone by ID
    # =========================================================
    @http.route('/api/zones/get/<int:zone_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_zone_by_id(self, zone_id, **kwargs):
        zone = request.env['zones'].sudo().browse(zone_id)
        if not zone.exists():
            return http.Response(json.dumps({'error': 'Zone not found'}), status=404, content_type='application/json')

        data = {
            'id': zone.id,
            'name': zone.name,
            'description': zone.description,
            'note': zone.note,
            'regions': zone.regions,
            'countries': zone.countries,
            'cities': zone.cities,
            'companies': [{'id': c.id, 'name': c.name} for c in z.company_ids],
        }
        return http.Response(json.dumps(data), content_type='application/json')

    # =========================================================
    # POST - create new zone
    # =========================================================
    @http.route('/api/zones/create', type='http', auth='public',
                methods=['POST'], csrf=False)
    def create_zone(self, **kwargs):
        import json

        # Parse JSON body
        try:
            data = json.loads(request.httprequest.data)
        except Exception:
            return http.Response(
                json.dumps({'error': 'Invalid JSON format'}),
                status=400,
                content_type='application/json'
            )

        # Validate required fields
        required_fields = ['name']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return http.Response(
                json.dumps({'error': f'Missing fields: {", ".join(missing)}'}),
                status=400,
                content_type='application/json'
            )

        # Create record
        zone = request.env['zones'].sudo().create({
            'name': data.get('name'),
            'description': data.get('description'),
            'note': data.get('note'),
            'regions': data.get('regions'),
            'countries': data.get('countries'),
            'cities': data.get('cities'),
            'company_ids': [(6, 0, data.get('company_ids', []))],
            'polygon_points': data.get('polygon_points'),
        })

        # Return JSON response
        return http.Response(
            json.dumps({'success': True, 'id': zone.id}),
            status=200,
            content_type='application/json'
        )

    # =========================================================
    # PUT - update existing zone
    # =========================================================
    @http.route('/api/zones/update/<int:zone_id>', type='json', auth='public', methods=['PUT'], csrf=False)
    def update_zone(self, zone_id, **post):
        zone = request.env['zones'].sudo().browse(zone_id)
        if not zone.exists():
            return {'error': 'Zone not found'}

        zone.sudo().write({
            'name': post.get('name', zone.name),
            'description': post.get('description', zone.description),
            'note': post.get('note', zone.note),
            'regions': post.get('regions', zone.regions),
            'countries': post.get('countries', zone.countries),
            'cities': post.get('cities', zone.cities),
            'company_ids': [(6, 0, post.get('company_ids', [c.id for c in zone.company_ids]))],
        })

        return {'success': True, 'id': zone.id}

    # =========================================================
    # DELETE - remove zone by ID
    # =========================================================
    @http.route('/api/zones/delete/<int:zone_id>', type='http', auth='public', methods=['DELETE'], csrf=False)
    def delete_zone(self, zone_id):
        zone = request.env['zones'].sudo().browse(zone_id)
        if not zone.exists():
            return http.Response(json.dumps({'error': 'Zone not found'}), status=404, content_type='application/json')

        zone.sudo().unlink()
        return http.Response(json.dumps({'success': True}), content_type='application/json')