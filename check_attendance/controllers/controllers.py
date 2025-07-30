import json
from pickle import FALSE
from odoo import http
from odoo.addons.test_impex.tests.test_load import message
from odoo.http import request , route

from odoo.http import Response


class users_id(http.Controller):
    # get user with his group name
    @http.route('/api/users', type='http', auth="public", methods=['GET'], csrf=False)
    def get_users(self):
        # Fetch all users and their groups
        users = request.env['res.users'].sudo().search([])
        user_data = []

        for user in users:
            # Get the user's groups
            groups = user.groups_id.mapped('name')
            user_data.append({
                'id': user.id,
                'name': user.name,
                "login": user.login,
                'groups': groups,
            })

        return request.make_response(json.dumps({'users': user_data}), headers={'Content-Type': 'application/json'})

    @http.route('/v1/user/get/user', methods=["GET"], auth="public", type="http", csrf=False)
    def getuser(self):

        try:
            user_ids = request.env['res.users'].sudo().search([])
            if not user_ids:
                return request.make_json_response({
                    "message": "there is no records",
                }, status=400)

            return request.make_json_response([{

                "id": user_id.id,
                "login": user_id.login,
                "group": user_id.groups_id,

            } for user_id in user_ids], status=200)
        except Exception as error:
            return request.make_json_response({
                "message": error,
            }, status=400)

    @http.route('/v1/user/get/group', methods=["GET"], auth="public", type="http", csrf=False)
    def getgroup(self):

        try:
            user_ids = request.env['res.groups'].sudo().search([])
            if not user_ids:
                return request.make_json_response({
                    "message": "there is no records",
                }, status=400)

            return request.make_json_response([{

                "id": user_id.id,
                "name": user_id.name

            } for user_id in user_ids], status=200)
        except Exception as error:
            return request.make_json_response({
                "message": error,
            }, status=400)

    #craete check attendance record
    # @http.route('/v1/create/check', methods=["POST"], auth="public", type="http", csrf=False)
    # def crete_json(self):
    #     # Decode the incoming JSON data
    #     args = request.httprequest.data.decode()
    #
    #     # Load the JSON data into a Python dictionary
    #     try:
    #         vals_list = json.loads(args)  # Expecting a list of dictionaries
    #     except json.JSONDecodeError:
    #         return request.make_response(
    #             json.dumps({"error": "Invalid JSON data"}),
    #             headers={'Content-Type': 'application/json'},
    #             status=400
    #         )
    #
    #     # Check if the input is a list
    #     if not isinstance(vals_list, list):
    #         return request.make_response(
    #             json.dumps({"error": "Input data must be a list of records"}),
    #             headers={'Content-Type': 'application/json'},
    #             status=400
    #         )
    #
    #     created_records = []
    #     errors = []
    #
    #     # Create the attendance records
    #     for vals in vals_list:
    #         try:
    #             user = request.env['check.attendance'].sudo().create(vals)
    #             created_records.append({
    #                 "name": user.name,
    #                 "x_in_note": user.x_in_note,
    #                 "x_out_note": user.x_out_note,
    #                 "employee_id": user.employee_id.id if user.employee_id else None,  # Get employee ID
    #                 # "employee_name": user.employee_id.name if user.employee_id else None,  # Get employee name
    #                 "check_in": user.check_in,
    #                 "check_out": user.check_out,
    #                 "check_in_map": user.check_in_map,
    #                 "check_out_map": user.check_out_map,
    #                 "employee_image": user.employee_image,
    #                 "place_image": user.place_image,
    #                 "user_in_image": user.user_in_image,
    #                 "place_in_image": user.place_in_image,
    #                 "user_out_image": user.user_out_image,
    #                 "place_out_image": user.place_out_image,
    #                 "update_api": user.update_api,
    #                 "employee_email": user.employee_email,
    #             })
    #         except Exception as e:
    #             errors.append({"error": str(e), "data": vals})
    #
    #     # Prepare the response data
    #     result = {
    #         "message": "Records processed",
    #         "created": created_records,
    #         "errors": errors
    #     }
    #
    #     # Return the response with a 201 status code if at least one record was created
    #     status_code = 201 if created_records else 400
    #     return request.make_response(
    #         json.dumps(result),
    #         headers={'Content-Type': 'application/json'},
    #         status=status_code
    #     )

    # @http.route('/v1/create/check', methods=["POST"], auth="public", type="http", csrf=False)
    # def crete_json(self):
    #     # Decode the incoming JSON data
    #     args = request.httprequest.data.decode()
    #
    #     # Load the JSON data into a Python dictionary
    #     try:
    #         vals_list = json.loads(args)  # Expecting a list of dictionaries
    #     except json.JSONDecodeError:
    #         return request.make_response(
    #             json.dumps({"error": "Invalid JSON data"}),
    #             headers={'Content-Type': 'application/json'},
    #             status=400
    #         )
    #
    #     # Check if the input is a list
    #     if not isinstance(vals_list, list):
    #         return request.make_response(
    #             json.dumps({"error": "Input data must be a list of records"}),
    #             headers={'Content-Type': 'application/json'},
    #             status=400
    #         )
    #
    #     created_records = []
    #     errors = []
    #
    #     # Create the attendance records
    #     for vals in vals_list:
    #         try:
    #             # Skip if no email provided
    #             if not vals.get('employee_email'):
    #                 errors.append({"error": "employee_email is required", "data": vals})
    #                 continue
    #
    #             # Search for employee by email
    #             employee = request.env['hr.employee'].sudo().search(
    #                 [('work_email', '=', vals.get('employee_email'))],
    #                 limit=1
    #             )
    #
    #             if not employee:
    #                 errors.append({
    #                     "error": f"No employee found with email {vals.get('employee_email')}",
    #                     "data": vals
    #                 })
    #                 continue
    #
    #             # Set the employee_id from the found employee
    #             vals['employee_id'] = employee.id
    #
    #             # Create the attendance record
    #             attendance = request.env['check.attendance'].sudo().create(vals)
    #
    #             created_records.append({
    #                 "id": attendance.id,
    #                 "name": attendance.name,
    #                 "x_in_note": attendance.x_in_note,
    #                 "x_out_note": attendance.x_out_note,
    #                 "employee_id": attendance.employee_id.id,
    #                 "check_in": attendance.check_in,
    #                 "check_out": attendance.check_out,
    #                 "check_in_map": attendance.check_in_map,
    #                 "check_out_map": attendance.check_out_map,
    #                 "employee_image": attendance.employee_image,
    #                 "place_image": attendance.place_image,
    #                 "user_in_image": attendance.user_in_image,
    #                 "place_in_image": attendance.place_in_image,
    #                 "user_out_image": attendance.user_out_image,
    #                 "place_out_image": attendance.place_out_image,
    #                 "update_api": attendance.update_api,
    #                 "employee_email": attendance.employee_email,
    #             })
    #
    #         except Exception as e:
    #             errors.append({
    #                 "error": str(e),
    #                 "data": vals
    #             })
    #
    #     # Prepare the response data
    #     result = {
    #         "message": "Records processed",
    #         "created_count": len(created_records),
    #         "error_count": len(errors),
    #         "created": created_records,
    #         "errors": errors
    #     }
    #
    #     # Return the response with a 201 status code if at least one record was created
    #     status_code = 201 if created_records else (400 if errors else 200)
    #     return request.make_response(
    #         json.dumps(result),
    #         headers={'Content-Type': 'application/json'},
    #         status=status_code
    #     )
    @http.route('/v1/create/check', methods=["POST"], auth="public", type="http", csrf=False)
    def crete_json(self):
        # Decode the incoming JSON data
        args = request.httprequest.data.decode()

        # Load the JSON data into a Python dictionary
        try:
            vals_list = json.loads(args)  # Expecting a list of dictionaries
        except json.JSONDecodeError:
            return request.make_response(
                json.dumps({"error": "Invalid JSON data"}),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        # Check if the input is a list
        if not isinstance(vals_list, list):
            return request.make_response(
                json.dumps({"error": "Input data must be a list of records"}),
                headers={'Content-Type': 'application/json'},
                status=400
            )

        created_records = []
        errors = []

        # Create the attendance records
        for vals in vals_list:
            try:
                # Skip if no email provided
                if not vals.get('employee_email'):
                    errors.append({"error": "employee_email is required", "data": vals})
                    continue

                # Search for employee by email
                employee = request.env['hr.employee'].sudo().search(
                    [('work_email', '=', vals.get('employee_email'))],
                    limit=1
                )

                if not employee:
                    errors.append({
                        "error": f"No employee found with email {vals.get('employee_email')}",
                        "data": vals
                    })
                    continue

                # Set the employee_id from the found employee
                vals['employee_id'] = employee.id

                # Create the attendance record
                attendance = request.env['check.attendance'].sudo().create(vals)

                # Prepare record data with proper datetime serialization
                record_data = {
                    "id": attendance.id,
                    "name": attendance.name,
                    "x_in_note": attendance.x_in_note,
                    "x_out_note": attendance.x_out_note,
                    "employee_id": attendance.employee_id.id,
                    "employee_email": attendance.employee_email,
                    "update_api": attendance.update_api,
                    # Convert datetime fields to ISO format strings
                    "check_in": attendance.check_in.isoformat() if attendance.check_in else None,
                    "check_out": attendance.check_out.isoformat() if attendance.check_out else None,
                    # Add other fields as needed
                }

                # Only include fields if they exist in the model
                optional_fields = [
                    'check_in_map', 'check_out_map', 'employee_image', 'place_image',
                    'user_in_image', 'place_in_image', 'user_out_image', 'place_out_image'
                ]

                for field in optional_fields:
                    if hasattr(attendance, field):
                        value = getattr(attendance, field)
                        # Handle binary fields if needed (might need base64 encoding)
                        record_data[field] = value

                created_records.append(record_data)

            except Exception as e:
                errors.append({
                    "error": str(e),
                    "data": vals
                })

        # Prepare the response data
        result = {
            "message": "Records processed",
            "created_count": len(created_records),
            "error_count": len(errors),
            "created": created_records,
            "errors": errors
        }

        # Return the response with a 201 status code if at least one record was created
        status_code = 201 if created_records else (400 if errors else 200)
        return request.make_response(
            json.dumps(result, default=str),  # Using default=str handles datetime serialization
            headers={'Content-Type': 'application/json'},
            status=status_code
        )
    # get check attendance record
    @http.route('/api/get/check_attendance', type='http', auth="public", methods=['GET'], csrf=False)
    def get_test(self):
        try:
            users = request.env['check.attendance'].sudo().search([('update_api', '=', False)])
            if not users:
                return request.make_json_response({
                    "error": "table is empty",
                }, status=400)
            return request.make_json_response([{
                "name": user.name,
                "id":user.id,
                "x_in_note": user.x_in_note,
                "x_out_note": user.x_out_note,
                "employee_id": user.employee_id.id if user.employee_id else None,  # Get employee ID
                "employee_name": user.employee_id.name if user.employee_id else None,  # Get employee name
                "check_in": user.check_in,
                "check_out": user.check_out,
                "check_in_map": user.check_in_map,
                "check_out_map": user.check_out_map,
                "employee_image": user.employee_image,
                "place_image": user.place_image,
                "user_in_image": user.user_in_image,
                "place_in_image": user.place_in_image,
                "user_out_image": user.user_out_image,
                "place_out_image": user.place_out_image,
                "update_api": user.update_api,
                "employee_email": user.employee_email,
            } for user in users], status=200)

        except Exception as error:
            return request.make_json_response({
                "error": error
            }, status=400)

    # check attendance check update record
    # Update endpoint for more than one record
    @http.route('/api/update/check/more', type='http', auth="public", methods=['PUT'], csrf=False)
    def update_test(self):
        # Decode the incoming data
        args = request.httprequest.data.decode()
        vals = json.loads(args)
        # Extract property IDs from the request
        property_ids = vals.get('check_attendance_ids', [])  # Expecting a list of IDs
        update_values = vals.get('update_values', {})  # Expecting a dictionary of values to update
        try:
            # If no property_ids are provided, fetch IDs of records with update_api = False
            if not property_ids:
                properties = request.env['check.attendance'].sudo().search([('update_api', '=', False)])
                property_ids = properties.ids  # Get the IDs of properties with update_api = False
            if not property_ids:
                return request.make_json_response({
                    "message": "No attendees IDs found with update_api set to False"
                }, status=404)
            # Fetch records based on the provided IDs
            properties = request.env['check.attendance'].sudo().search([('id', 'in', property_ids)])
            if not properties:
                return request.make_json_response({
                    "message": "No records found for the provided IDs"
                }, status=404)
            # Update each record with the provided values
            # Ensure that update_values contains update_api set to True
            update_values['update_api'] = True  # Set update_api to True
            properties.write(update_values)
            # Prepare a response with updated record details
            updated_records = [{
                "id": user.id,
                "name": user.name,
                "update_api": user.update_api,
                "x_in_note": user.x_in_note,
                "x_out_note": user.x_out_note,
            } for user in properties]
            return request.make_json_response({
                "message": "Records updated successfully",
                "updated_records": updated_records
            }, status=200)
        except Exception as error:
            return request.make_json_response({
                "error": str(error)
            }, status=400)
    # update endpoint
    @http.route('/api/update/check/attendance/<int:check_id>/<string:employee_email>', type='http', auth="public", methods=['PUT'], csrf=False)
    def update_test_one(self,check_id,employee_email):
        check_id = request.env['check.attendance'].sudo().search([('id', '=', check_id),
                                                        ('employee_email', '=', employee_email)])
        args = request.httprequest.data.decode()
        vals = json.loads(args)
        try:
            if not check_id:
                return request.make_json_response({
                    "message": "id does not exist"
                }, status=400)
            check_id.write(vals)
            return request.make_json_response({
                "message" : "record updated successfully",
                "id" : check_id.id,
                "name" : check_id.name,
                "x_in_note": check_id.x_in_note,
                "x_out_note": check_id.x_out_note,
                "employee_id": check_id.employee_id.id if check_id.employee_id else None,  # Get employee ID
                # "employee_name": check_id.employee_id.name if check_id.employee_id else None,  # Get employee name
                "check_in": check_id.check_in,
                "check_out": check_id.check_out,
                "check_in_map": check_id.check_in_map,
                "check_out_map": check_id.check_out_map,
                "employee_image": check_id.employee_image,
                "place_image": check_id.place_image,
                "user_in_image": check_id.user_in_image,
                "place_in_image": check_id.place_in_image,
                "user_out_image": check_id.user_out_image,
                "place_out_image": check_id.place_out_image,
                "update_api": check_id.update_api
            },status= 200)

        except Exception as error:
            return request.make_json_response({
                "error" : error
            },status=400)
    #create one record
    # create check attendance record
    # @http.route('/v1/create/check/one', methods=["POST"], auth="public", type="http", csrf=False)
    # def post_one_record(self):
    #     args=request.httprequest.data.decode()
    #     vals = json.loads(args)
    #     if not vals.get("employee_email"):
    #         return request.make_json_response({
    #             "message": "employee email is required"
    #         }, status=400)
    #
    #     # if not vals.get("employee_id"):
    #     #     return request.make_json_response({
    #     #         "message": "emp_id is required"
    #     #     }, status=400)
    #
    #     try:
    #         res=request.env['check.attendance'].sudo().create(vals)
    #         if res:
    #             return request.make_json_response({
    #                 "message" : "record has been posted",
    #                 "id": res.id,
    #                 "name": res.name,
    #                 "x_in_note": res.x_in_note,
    #                 "x_out_note": res.x_out_note,
    #                 "employee_id": res.employee_id.id if res.employee_id else None,
    #                 "check_in": res.check_in,
    #                 "check_out": res.check_out,
    #                 "check_in_map": res.check_in_map,
    #                 "check_out_map": res.check_out_map,
    #                 "employee_image": res.employee_image,
    #                 "place_image": res.place_image,
    #                 "user_in_image": res.user_in_image,
    #                 "place_in_image": res.place_in_image,
    #                 "user_out_image": res.user_out_image,
    #                 "place_out_image": res.place_out_image,
    #                 "update_api": res.update_api,
    #                 "employee_email": res.employee_email,
    #
    #             },status=201)
    #     except Exception as error:
    #         return request.make_json_response({
    #             "message" : error
    #         },status=400)


# create check attendance based on employee_id
    @http.route('/v1/create/check/one', methods=["POST"], auth="public", type="http", csrf=False)
    def post_one_record(self):
        args = request.httprequest.data.decode()
        vals = json.loads(args)

        if not vals.get("employee_email"):
            return request.make_json_response({
                "message": "employee email is required"
            }, status=400)

        try:
            # Search for employee by email
            employee = request.env['hr.employee'].sudo().search([('work_email', '=', vals.get("employee_email"))],
                                                                limit=1)

            if not employee:
                return request.make_json_response({
                    "message": "No employee found with this email"
                }, status=404)

            # Set the employee_id in the vals before creating
            vals['employee_id'] = employee.id

            res = request.env['check.attendance'].sudo().create(vals)
            if res:
                return request.make_json_response({
                    "message": "record has been posted",
                    "id": res.id,
                    "name": res.name,
                    "x_in_note": res.x_in_note,
                    "x_out_note": res.x_out_note,
                    "employee_id": res.employee_id.id if res.employee_id else None,
                    "check_in": res.check_in,
                    "check_out": res.check_out,
                    "check_in_map": res.check_in_map,
                    "check_out_map": res.check_out_map,
                    "employee_image": res.employee_image,
                    "place_image": res.place_image,
                    "user_in_image": res.user_in_image,
                    "place_in_image": res.place_in_image,
                    "user_out_image": res.user_out_image,
                    "place_out_image": res.place_out_image,
                    "update_api": res.update_api,
                    "employee_email": res.employee_email,
                }, status=201)

        except Exception as error:
            return request.make_json_response({
                "message": str(error)
            }, status=400)

    @http.route('/v1/api/get/user/<int:user_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def get_user_and_groups(self, user_id):
        # Fetch the user based on user_id
        user = request.env['res.users'].sudo().browse(user_id)
        if not user.exists():
            return request.make_response('User  not found', status=404)

        # Get user details
        user_info = {
            'id': user.id,
            # 'name': user.name,
            'email': user.email,
            'groups': []
        }

        # Get user groups
        groups = user.groups_id
        for group in groups:
            user_info['groups'].append({
                # 'id': group.id,
                'name': group.name,
            })

        return request.make_response(json.dumps(user_info), headers={'Content-Type': 'application/json'})

    #update with get
    @http.route('/api/update_records', type='http', auth='public', methods=['GET'], csrf=False)
    def update_records(self):
        # Fetch records where update_api is False
        records = request.env['check.attendance'].sudo().search([('update_api', '=', False)])
        # Update the records to set update_api to True
        if records:
            records.write({'update_api': True})
        # Prepare response
        response_data = {
            # 'updated_count': len(records),
            # 'records': [{'id': record.id, 'name': record.name} for record in records]
        }

        # return request.make_response(response_data, headers={'Content-Type': 'application/json'})
        return request.make_json_response([{
            "id": user_id.id,
            "name": user_id.name

        } for user_id in records], status=200)

    #update employee records

    @http.route('/api/update_records/employee', type='http', auth='public', methods=['GET'], csrf=False)
    def update_records(self):
        # Fetch records where update_api is False
        records = request.env['hr.employee'].sudo().search([('update_api', '=', False)])
        # Update the records to set update_api to True
        if records:
            records.write({'update_api': True})
        # Prepare response

        return request.make_json_response([{
            "id": user_id.id,
            "name": user_id.name,
            "work_email":user_id.work_email,
            # "update_api":user_id.update_api

        } for user_id in records], status=200)





