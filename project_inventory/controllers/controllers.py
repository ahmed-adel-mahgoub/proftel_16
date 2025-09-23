# -*- coding: utf-8 -*-
# from odoo import http


# class ProjectInventory(http.Controller):
#     @http.route('/project_inventory/project_inventory', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/project_inventory/project_inventory/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('project_inventory.listing', {
#             'root': '/project_inventory/project_inventory',
#             'objects': http.request.env['project_inventory.project_inventory'].search([]),
#         })

#     @http.route('/project_inventory/project_inventory/objects/<model("project_inventory.project_inventory"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('project_inventory.object', {
#             'object': obj
#         })
