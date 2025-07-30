import json
from datetime import datetime
from pickle import FALSE

from odoo import http, fields

from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class testApi(http.Controller):
    # create method should have required field to create record
    @http.route('/v1/api/arduino/create',methods=["POST"],auth="public",type="http",csrf=False)
    def post_arduino(self):
        args= request.httprequest.data.decode()
        vals= json.loads(args)
        if not vals.get('name'):
            return request.make_json_response({
                "message": "name is required!",

            }, status=400)
        try:
            res = request.env['test.api'].sudo().create(vals)
            if res:
                return request.make_json_response({
                    "message" : "test_api has been created successfully ",
                    "name": res.name,
                    "test_integer" : res.test_integer,

                },status=201)
        except Exception as error:
            return request.make_json_response({
                "message": error,
            }, status=400 )

    @http.route('/v1/api/arduino/get', type='http', auth="custom_auth", methods=['GET'], csrf=False)
    def get_arduino(self):
        try:
            users = request.env['test.api'].sudo().search([])
            if not users:
                return request.make_json_response({
                    "error": "table is empty",
                }, status=400)
            return request.make_json_response([{
                "id": user.id,
                "name": user.name,
                "test_integer": user.test_integer,
            } for user in users], status=200)

        except Exception as error:
            return request.make_json_response({
                "error": error
            }, status=400)



    @http.route('/v1/api/get/employee/user/<string:x_app_username>', type='http', auth='custom_auth', methods=['GET'],
                csrf=False)
    # 6e0823e296a8f8f585c7b22765d5d7d2f79298fc     8090
    def get_employee_app(self, x_app_username):
        # Fetch the employee based on work_email
        employee = request.env['hr.employee'].sudo().search([('x_app_username', '=', x_app_username)], limit=1)

        if not employee:
            return request.make_response('Employee not found', status=404)

        # Get user details
        user_info = {
            'id': employee.id,
            'name': employee.name,
            'x_app_password': employee.x_app_password,
            'x_app_username': employee.x_app_username,
            'department_id': employee.department_id.id,
            'user_id': employee.user_id.id,
            'work_email': employee.work_email,
            'sender_id':employee.sender_id
        }

        return request.make_response(json.dumps(user_info), headers={'Content-Type': 'application/json'})


    @http.route('/v1/api/get/attendance/record/<string:employee_email>/<string:check_in_dt>'
        , type='http', auth='public'
        , methods=['GET'], csrf=False)
    def get_attendance_appa(self, employee_email,check_in_dt):
        try:
            check_in_dt = datetime.strptime(check_in_dt, '%Y-%m-%d %H:%M:%S')

        except ValueError:
            return request.make_response('Invalid date format. Use yy-mm-dd HH:MM:SS', status=400)

        # Search for attendance records based on the employee email and check-in date
        attendance_records = request.env['check.attendance'].sudo().search([
            ('employee_email', '=', employee_email),
            ('check_in', '=', check_in_dt)
        ])

        if not attendance_records:
            return request.make_response('Attendance not found', status=404)

        # Prepare user details
        users = []
        for record in attendance_records:
            users.append({
                'id': record.id,
                'name': record.name,
            })

        return request.make_response(json.dumps(users), headers={'Content-Type': 'application/json'})

