# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_inscription_ids = fields.One2many('payment.inscription', "inscription_id", compute="get_payment_inscription_ids", store=False)
    remain_to_pay_ariary = fields.Float("Reste à payer en Ariary", related='inscription_id.remain_to_pay_ariary')
    remain_to_pay_euro = fields.Float("Reste à payer en Euro", related="inscription_id.remain_to_pay_euro")
    invoice_date = fields.Date(readonly=True, string="Invoice Date", compute="set_invoice_date", store=True)

    @api.depends('payment_inscription_ids')
    def set_invoice_date(self):
        print('_'*100)
        for record in self:
            max_date = ''
            for payment in record.payment_inscription_ids:
                if not max_date:
                    max_date = payment.date
                if payment.date > max_date:
                    max_date = payment.date

            record.invoice_date = max_date

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

    payment_inscription_ids = fields.One2many('payment.inscription', "inscription_id",)