# -*- coding: utf-8 -*-
# from odoo import http


# class IndexCustomCnam(http.Controller):
#     @http.route('/index_custom_cnam/index_custom_cnam/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/index_custom_cnam/index_custom_cnam/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('index_custom_cnam.listing', {
#             'root': '/index_custom_cnam/index_custom_cnam',
#             'objects': http.request.env['index_custom_cnam.index_custom_cnam'].search([]),
#         })

#     @http.route('/index_custom_cnam/index_custom_cnam/objects/<model("index_custom_cnam.index_custom_cnam"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('index_custom_cnam.object', {
#             'object': obj
#         })
