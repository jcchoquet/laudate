# -*- coding: utf-8 -*-
# from odoo import http


# class Laudate(http.Controller):
#     @http.route('/laudate/laudate/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/laudate/laudate/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('laudate.listing', {
#             'root': '/laudate/laudate',
#             'objects': http.request.env['laudate.laudate'].search([]),
#         })

#     @http.route('/laudate/laudate/objects/<model("laudate.laudate"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('laudate.object', {
#             'object': obj
#         })
