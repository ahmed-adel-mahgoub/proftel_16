# -*- coding: utf-8 -*-
# from odoo import http


# class WssTest(http.Controller):
#     @http.route('/wss_test/wss_test', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/wss_test/wss_test/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('wss_test.listing', {
#             'root': '/wss_test/wss_test',
#             'objects': http.request.env['wss_test.wss_test'].search([]),
#         })

#     @http.route('/wss_test/wss_test/objects/<model("wss_test.wss_test"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('wss_test.object', {
#             'object': obj
#         })
