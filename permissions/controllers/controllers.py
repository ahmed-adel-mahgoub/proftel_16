# -*- coding: utf-8 -*-
# from odoo import http


# class Permissions(http.Controller):
#     @http.route('/permissions/permissions', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/permissions/permissions/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('permissions.listing', {
#             'root': '/permissions/permissions',
#             'objects': http.request.env['permissions.permissions'].search([]),
#         })

#     @http.route('/permissions/permissions/objects/<model("permissions.permissions"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('permissions.object', {
#             'object': obj
#         })
