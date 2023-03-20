# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import OrderedDict

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request
from odoo.exceptions import AccessError, MissingError


class IndexCustomCnam(CustomerPortal):
    # @http.route('/index_custom_cnam/update_cost', auth='public')
    # def index(self, **kw):
    #     costs = http.request.env['unit.enseigne.config.cost'].sudo().search([])
    #     costs.update_currency_cost()

    #     ue = http.request.env['unit.enseigne'].sudo().search([])
    #     ue.update_currency_cost()
    #     return "all cost updated"


    # @http.route('/index_custom_cnam/update_payment_term', auth='public')
    # def update_payment_term(self, **kw):
    #     invoice_ids = http.request.env['account.move'].sudo().search([])
    #     for invoice_id in invoice_ids:
    #         max_date = ''
    #         for pi in invoice_id.payment_inscription_ids:
    #             if not max_date:
    #                 max_date = pi.date
    #             if pi.date > max_date:
    #                 max_date = pi.date
    #         if max_date:
    #             invoice_id.write({
    #                 'invoice_payment_term_id': None,
    #                 'invoice_date_due': max_date
    #             })

    #     return "Dates updated"

    @http.route('/index_custom_cnam/update_regrouping_date', auth='public')
    def update_regrouping_date(self, **kw):
        line_ids = request.env['regrouping.center.line'].sudo().search([('grouping_date','=', None)])
        for line in line_ids:
            if line.regrouping_id and line.regrouping_id.date:
                line.write({'grouping_date': line.regrouping_id.date})

        return "Thanks! All date updated."

    @http.route(['/my/cnam_documents'], type='http', auth="user", website=True)
    def portal_cnam_documents(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):

        values = self._prepare_portal_layout_values()
        note_obj = request.env['note.list'].sudo()

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }

        if not filterby:
            filterby = 'all'
        domain = searchbar_filters.get(filterby, searchbar_filters.get('all'))['domain']

        archive_groups = self._get_archive_groups('note.list', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        domain += [('partner_id', '=', request.env.user.partner_id.id)]

        domain += [('validation', '=', 'validated')]
        # count for pager
        note_count = note_obj.search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/note",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby,},
            total=note_count,
            page=page,
            step=self._items_per_page
        )
        # content according to pager and archive selected
        note_ids = note_obj.search(domain, order=None, limit=self._items_per_page, offset=pager['offset'])
        attestation_ok = []
        group_att = request.env['note.list'].sudo()
        for note in note_ids:
            vals_att = {'etudiant': note.partner_id.id,
                        'as': note.note_list_filter_id.year.id
                        }
            if vals_att not in attestation_ok:
                attestation_ok.append(vals_att)
                group_att |= note


        values.update({
            'date': date_begin,
            'note_ids': group_att,
            'page_name': 'Note',
            'pager': pager,
            'archive_groups': archive_groups,
            'default_url': '/my/note',
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
        })
        return request.render("index_custom_cnam.portal_cnam_documents", values)