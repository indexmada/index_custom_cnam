# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    @api.depends('payment_inscription_ids.date')
    def set_invoice_payment_term_date(self):
        for record in self:
            print('*'*100)
            max_date = ''
            for payment in record.payment_inscription_ids:
                if not max_date:
                    max_date = payment.date
                if payment.date > max_date:
                    max_date = payment.date
            if max_date:
                record.invoice_date_due = max_date

    payment_inscription_ids = fields.One2many('payment.inscription', "inscription_id", compute="get_payment_inscription_ids", store=False)
    remain_to_pay_ariary = fields.Float("Reste à payer en Ariary", related='inscription_id.remain_to_pay_ariary')
    remain_to_pay_euro = fields.Float("Reste à payer en Euro", related="inscription_id.remain_to_pay_euro")
    invoice_date_due = fields.Date(string='Due Date', readonly=True, index=True, copy=False,
        states={'draft': [('readonly', False)]}, store=True, default=set_invoice_payment_term_date, compute="set_invoice_payment_term_date")

    def get_payment_inscription_ids(self):
        for record in self:
            payment_inscription_obj = self.env['payment.inscription'].sudo()
            all_payments = record.inscription_id.payment_inscription_ids
            for payment in all_payments:
                if payment.currency_id == record.currency_id:
                    payment_inscription_obj |= payment

            record.payment_inscription_ids = payment_inscription_obj


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def get_ctx(self):
        payment_inscription_obj = self.env['payment.inscription'].sudo()
        pi_ids = []
        for invoice in self.invoice_ids:
            if invoice.payment_inscription_ids:
                for pi in invoice.payment_inscription_ids:
                    pi_ids.append(int(pi.id))
        return [('id','in', pi_ids)]

    payment_inscription_ids = fields.Many2many('payment.inscription', string="Payment Inscription")
    

    @api.onchange('payment_inscription_ids')
    def pi_change(self):
        for record in self:
            amount = 0
            for pi in record.payment_inscription_ids:
                amount += pi.cost_devise

            record.amount = amount



class PaymentInscription(models.Model):
    _inherit = 'payment.inscription'

    payment_state = fields.Boolean("Payé",compute="get_payment_statut")

    def get_payment_statut(self):
        for record in self:
            pi_ids = self.env['account.payment'].sudo().search([('state', '!=', 'draft')]).mapped('payment_inscription_ids')
            if record in pi_ids:
                record.payment_state = True
            else:
                record.payment_state = False