import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


import io
from ast import literal_eval

import xlsxwriter as xlsxwriter

from datetime import date

class XLSXReportController(http.Controller):
    @http.route('/xlsx_reports', type='http', auth='public')
    def get_report_xlsx(self, start_date=False, end_date=False, get_model=False, semester_ids=False, filename="_", statement_id = False):

        if end_date == 'False':
            end_date = False
        if get_model == 'False':
            get_model = False
        if semester_ids == 'False':
            semester_ids = False
        if filename == 'False':
            filename = False
        

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        data = {
            'start_date': start_date,
            'end_date': end_date,
            'get_model': get_model,
            'semester_ids': semester_ids,
            'statement_id': statement_id
        }

        request.env['example.xlsx.report.wizard'].sudo().get_xlsx_report(workbook, data)  

        workbook.close()
        output.seek(0)
        xlsheader = [('Content-Type', 'application/octet-stream'),
                     ('Content-Disposition', 'attachment; filename=%s;' % filename)]
        return request.make_response(output, xlsheader)
