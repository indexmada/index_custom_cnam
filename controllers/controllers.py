# -*- coding: utf-8 -*-
from odoo import http


class IndexCustomCnam(http.Controller):
    # @http.route('/index_custom_cnam/update_cost', auth='public')
    # def index(self, **kw):
    #     costs = http.request.env['unit.enseigne.config.cost'].sudo().search([])
    #     costs.update_currency_cost()

    #     ue = http.request.env['unit.enseigne'].sudo().search([])
    #     ue.update_currency_cost()
    #     return "all cost updated"


    @http.route('/index_custom_cnam/update_payment_term', auth='public')
    def update_payment_term(self, **kw):
        invoice_ids = http.request.env['account.move'].sudo().search([])
        for invoice_id in invoice_ids:
            max_date = ''
            for pi in invoice_id.payment_inscription_ids:
                if not max_date:
                    max_date = pi.date
                if pi.date > max_date:
                    max_date = pi.date
            if max_date:
                invoice_id.write({
                    'invoice_payment_term_id': None,
                    'invoice_date_due': max_date
                })

        return "Dates updated"