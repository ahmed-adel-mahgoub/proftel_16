# -*- coding: utf-8 -*-
# from odoo import http


# class PosAddDiscount(http.Controller):
#     @http.route('/pos_add_discount/pos_add_discount', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_add_discount/pos_add_discount/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_add_discount.listing', {
#             'root': '/pos_add_discount/pos_add_discount',
#             'objects': http.request.env['pos_add_discount.pos_add_discount'].search([]),
#         })

#     @http.route('/pos_add_discount/pos_add_discount/objects/<model("pos_add_discount.pos_add_discount"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_add_discount.object', {
#             'object': obj
#         })

