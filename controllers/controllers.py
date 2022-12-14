# -*- coding: utf-8 -*-
from odoo import http


class IndexCustomCnam(http.Controller):
    @http.route('/index_custom_cnam/update_cost', auth='public')
    def index(self, **kw):
        costs = http.request.env['unit.enseigne.config.cost'].sudo().search([])
        costs.update_currency_cost()

        ue = http.request.env['unit.enseigne'].sudo().search([])
        ue.update_currency_cost()
        return "all cost updated"



