# -*- coding: utf-8 -*-
# from odoo import http


# class SolveEmpMdule(http.Controller):
#     @http.route('/solve_emp_mdule/solve_emp_mdule', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/solve_emp_mdule/solve_emp_mdule/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('solve_emp_mdule.listing', {
#             'root': '/solve_emp_mdule/solve_emp_mdule',
#             'objects': http.request.env['solve_emp_mdule.solve_emp_mdule'].search([]),
#         })

#     @http.route('/solve_emp_mdule/solve_emp_mdule/objects/<model("solve_emp_mdule.solve_emp_mdule"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('solve_emp_mdule.object', {
#             'object': obj
#         })
