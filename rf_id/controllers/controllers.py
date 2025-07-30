# -*- coding: utf-8 -*-
# from odoo import http


# class RfId(http.Controller):
#     @http.route('/rf_id/rf_id', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rf_id/rf_id/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rf_id.listing', {
#             'root': '/rf_id/rf_id',
#             'objects': http.request.env['rf_id.rf_id'].search([]),
#         })

#     @http.route('/rf_id/rf_id/objects/<model("rf_id.rf_id"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rf_id.object', {
#             'object': obj
#         })
