# -*- coding: utf-8 -*-
# from odoo import http


# class HrEmployeeSenderId(http.Controller):
#     @http.route('/hr_employee_sender_id/hr_employee_sender_id', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_employee_sender_id/hr_employee_sender_id/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_employee_sender_id.listing', {
#             'root': '/hr_employee_sender_id/hr_employee_sender_id',
#             'objects': http.request.env['hr_employee_sender_id.hr_employee_sender_id'].search([]),
#         })

#     @http.route('/hr_employee_sender_id/hr_employee_sender_id/objects/<model("hr_employee_sender_id.hr_employee_sender_id"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_employee_sender_id.object', {
#             'object': obj
#         })
