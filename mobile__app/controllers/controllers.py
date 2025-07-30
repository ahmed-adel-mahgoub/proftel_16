# -*- coding: utf-8 -*-
# from odoo import http


# class MobileApp(http.Controller):
#     @http.route('/mobile__app/mobile__app', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mobile__app/mobile__app/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mobile__app.listing', {
#             'root': '/mobile__app/mobile__app',
#             'objects': http.request.env['mobile__app.mobile__app'].search([]),
#         })

#     @http.route('/mobile__app/mobile__app/objects/<model("mobile__app.mobile__app"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mobile__app.object', {
#             'object': obj
#         })
