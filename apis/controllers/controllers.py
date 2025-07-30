import json
from datetime import datetime
from pickle import FALSE

from odoo import http, fields

from odoo.http import request
import logging

_logger = logging.getLogger(__name__)
class Apis(http.Controller):
    @http.route('/v1/api/attendance/get/email/<string:work_email>', type='http', auth="public", methods=['GET'], csrf=False)
    def get_attendance_email(self,work_email):
        try:
            users = request.env['hr.attendance'].sudo().search([('email', '=', work_email)])
            if not users:
                return request.make_json_response({
                    "error": "table is empty",
                }, status=400)
            return request.make_json_response([{
                "id": user.id,
                "employee_id": user.employee_id.name,
                "work_email": user.email,
            } for user in users], status=200)

        except Exception as error:
            return request.make_json_response({
                "error": error
            }, status=400)

    # @http.route('/v1/api/attendance/get', type='http', auth="public", methods=['GET'], csrf=False)
    # def get_attendance_email_all(self, **kwargs):
    #     try:
    #         # Get all attendance records
    #         attendances = request.env['hr.attendance'].sudo().search([])
    #
    #         if not attendances:
    #             return request.make_json_response({
    #                 "message": "No attendance records found",
    #                 "count": 0,
    #                 "data": []
    #             }, status=200)
    #
    #         # Prepare response data
    #         result = []
    #         for attendance in attendances:
    #             employee = attendance.employee_id
    #             result.append({
    #                 "attendance_id": attendance.id,
    #                 "employee": {
    #                     "id": employee.id,
    #                     "name": employee.name,
    #                     "work_email": employee.work_email,
    #                     "department": employee.department_id.name if employee.department_id else None,
    #
    #                     }})
    #
    #
    #         return request.make_json_response({
    #             "message": "Attendance records retrieved successfully",
    #             "count": len(attendances),
    #             "data": result
    #         }, status=200)
    #
    #     except Exception as error:
    #         return request.make_json_response({
    #             "error": str(error),
    #             "message": "Failed to retrieve attendance records"
    #         }, status=400)
    @http.route('/v1/api/attendance/get/all', type='http', auth="public", methods=['GET'], csrf=False)
    def get_attendance_email_all(self, **kwargs):
        try:
            # Get all attendance records
            attendances = request.env['hr.attendance'].sudo().search([])

            if not attendances:
                return request.make_json_response({
                    "message": "No attendance records found",
                    "count": 0,
                    "data": []
                }, status=200)

            # Prepare response data
            result = []
            for attendance in attendances:
                employee = attendance.employee_id
                result.append({
                    "attendance_id": attendance.id,
                    "employee": {
                        "id": employee.id,
                        "name": employee.name,
                        "work_email": employee.work_email,
                        "department": employee.department_id.name if employee.department_id else None,
                    },
                    "check_in": attendance.check_in if attendance.check_in else None,
                    "check_out": attendance.check_out if attendance.check_out else None,
                    "worked_hours": attendance.worked_hours if attendance.worked_hours else 0,
                    "employee_image": attendance.employee_image,
                    "place_image": attendance.place_image,
                    "user_in_image": attendance.user_in_image,
                    "place_in_image": attendance.place_in_image,
                    "user_out_image": attendance.user_out_image,
                    "place_out_image": attendance.place_out_image,
                    "lat_check_in": attendance.lat_check_in,
                    "long_check_in": attendance.long_check_in,
                    "lat_check_out": attendance.lat_check_out,
                    "check_in_map": attendance.check_in_map,
                    "check_out_map": attendance.check_out_map,
                    "x_check_out_map": attendance.x_check_out_map,
                    "x_check_in_map": attendance.x_check_in_map,
                    "x_mobile": attendance.x_mobile,
                    "check_attendance_id": attendance.check_attendance_id,

                })
            return request.make_json_response({
                "message": "Attendance records retrieved successfully",
                "count": len(attendances),
                "data": result
            }, status=200)

        except Exception as error:
            return request.make_json_response({
                "error": str(error),
                "message": "Failed to retrieve attendance records"
            }, status=400)