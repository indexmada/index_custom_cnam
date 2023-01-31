import time
import json
import io
from datetime import date
from odoo import fields, http, models, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
class ExcelWizard(models.TransientModel):
    _name = "example.xlsx.report.wizard"
    start_date = fields.Date(string="Start Date", default=date.today(), required=True)
    end_date = fields.Date(string="End Date", default=date.today(), required=True)
    def print_xlsx(self):
        if self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'example.xlsx.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                    }
        }
    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        top_column_format = workbook.add_format({'font_size': '13px', 'bold':True})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'20px'})
        txt = workbook.add_format({'font_size': '10px'})

        # sheet.merge_range('B2:I3', 'EXCEL REPORT', head)
        # sheet.write('B6', 'From:', cell_format)

        sheet.merge_range('A1:I2', "INSCRIPTION ET REINSCRIPTION", head)
        column = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','R','S','T','U','V','W','X','Y','Z']
        top_column = ['Auditeur', 'Civilité', 'Nom', 'Nom Marital', 'Prénom', 'Date de naissance', 'Mail', 'Diplôme','UE1','UE2','UE3','UE4','UE5','UE6','UE7','UE8']
        
        sheet.merge_range('A4:I4', 'Arrêtée le:'+str(date.today()), top_column_format)

        line = 5
        count = 0
        for content in top_column:
            cell = column[count]+str(line)
            sheet.write(cell, content, top_column_format)
            count +=1

        line +=1
        inscription_ids = self.env['inscription.edu'].sudo().search([('date', '>=', data['start_date']), ('date','<=', data['end_date'])])
        for insc in inscription_ids:
            count = 0

            # Auditeur
            cell = column[count]+str(line)
            sheet.write(cell, insc.name, cell_format) 

            # Civilité
            if insc.civilite == 'mr':
                civilite = 'Monsieur'
            elif insc.civilite == 'mll':
                civilite = 'Mademoiselle'
            elif insc.civilite == 'mme':
                civilite = 'Madame'
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, civilite, cell_format)

            # Nom
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.surname, cell_format)

            # Nom marital
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.name_marital, cell_format)

            # Prénom
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.firstname, cell_format)

            # Date de naissance
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, str(insc.date_of_birth), cell_format)

            # Mail
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.email, cell_format)

            # Diplôme
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.foreign_diploma, cell_format)

            # UEs
            for ue in insc.units_enseignes:
                count+=1
                cell = column[count]+str(line)
                sheet.write(cell, ue.name.display_name, cell_format)
            # Other UEs
            for ue in insc.other_ue_ids:
                count+=1
                cell = column[count]+str(line)
                sheet.write(cell, ue.name.display_name, cell_format)
            line +=1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()