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

XLSX_COLUMN = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','R','S','T','U','V','W','X','Y','Z']
class AccountBankaStatement(models.Model):
    _inherit = "account.bank.statement"

    def print_xlsx(self):
        data = {
            'statement_id': self.id,
        }
        return {
            'type': 'ir_actions_xlsx_download',
            'data': {'model': 'example.xlsx.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Excel Report',
                    }
        }   
        

class ExcelWizard(models.TransientModel):
    _name = "example.xlsx.report.wizard"
    start_date = fields.Date(string="Start Date", default=date.today(), required=True)
    end_date = fields.Date(string="End Date", default=date.today(), required=False)
    get_model = fields.Char(string="Model", required=False)
    def print_xlsx(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'get_model': self.get_model,
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
        if data.get('statement_id'):
            self.get_xlsx_report_caisse_by_statement(data, response)
        elif data.get('get_model') and data['get_model'] == 'rel_caisse':
            self.get_xlsx_report_rel_caisse(data, response)
        elif data.get('end_date'):
            self.get_xlsx_report_inscription(data, response)
        else:
            self.get_xlsx_report_grouping(data, response)

    def get_xlsx_report_caisse_by_statement(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        top_column_format = workbook.add_format({'font_size': '13px', 'bold':True})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'14px'})
        txt = workbook.add_format({'font_size': '10px'})       
        
        statement = self.env['account.bank.statement'].sudo().browse(int(data.get('statement_id')))

        sheet.merge_range('A1:D2', "RELEVE DE CAISSE: "+statement.journal_id.name, head)
        column = XLSX_COLUMN
        top_column = ['Réference', 'Libellé', 'Débit', 'Crédit']

        line = 5
        count = 0
        for content in top_column:
            cell = column[count]+str(line)
            sheet.write(cell, content, top_column_format)
            count +=1

        line +=1
        amount_debit = 0
        amount_credit = 0

        for line_id in statement.mapped('line_ids'):
            count = 0

            # Réference
            cell = column[count]+str(line)
            sheet.write(cell, line_id.ref, cell_format)

            # Libellé
            count +=1
            cell = column[count]+str(line)
            sheet.write(cell, line_id.name, cell_format)

            # Débit (Les montants Négatif) Crédit (Les montants Positifs)
            if line_id.amount < 0:
                count+=1
                amount = abs(line_id.amount)
                amount_debit += amount
            else:
                count+=2
                amount = line_id.amount
                amount_credit += amount
            cell = column[count]+str(line)
            sheet.write(cell, amount, cell_format)

            line +=1

        # Total
        count = 0
        cell = column[count]+str(line)
        sheet.write(cell, 'Total', top_column_format)
        count +=2
        cell = column[count]+str(line)
        sheet.write(cell, amount_debit, top_column_format)
        count +=1
        cell = column[count]+str(line)
        sheet.write(cell, amount_credit, top_column_format)

        # Total Chèque + Bank
        line +=1
        count= 0
        cell = column[count]+str(line)
        sheet.write(cell, '', top_column_format)
        count += 3
        cell = column[count]+str(line)
        sheet.write(cell, abs(amount_debit - amount_credit), top_column_format)


        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report_rel_caisse(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        top_column_format = workbook.add_format({'font_size': '13px', 'bold':True})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'14px'})
        txt = workbook.add_format({'font_size': '10px'})       

        sheet.merge_range('A1:D2', "RELEVE DE CAISSE", head)
        column = XLSX_COLUMN
        top_column = ['Réference', 'Libellé', 'Débit', 'Crédit']

        line = 5
        count = 0
        for content in top_column:
            cell = column[count]+str(line)
            sheet.write(cell, content, top_column_format)
            count +=1

        line +=1
        amount_debit = 0
        amount_credit = 0

        line_ids = self.env['account.bank.statement.line'].sudo().search([('date', '>=', data['start_date']), ('date','<=', data['end_date'])])
        for line_id in line_ids:
            count = 0

            # Réference
            cell = column[count]+str(line)
            sheet.write(cell, line_id.ref, cell_format)

            # Libellé
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, line_id.name, cell_format)

            # Débit (Les montants Négatif) Crédit (Les montants Positifs)
            if line_id.amount < 0:
                count+=1
                amount = abs(line_id.amount)
                amount_debit += amount
            else:
                count+=2
                amount = line_id.amount
                amount_credit += amount
            cell = column[count]+str(line)
            sheet.write(cell, amount, cell_format)

            line +=1

        # Total
        count = 0
        cell = column[count]+str(line)
        sheet.write(cell, 'Total', top_column_format)
        count +=2
        cell = column[count]+str(line)
        sheet.write(cell, amount_debit, top_column_format)
        count +=1
        cell = column[count]+str(line)
        sheet.write(cell, amount_credit, top_column_format)

        # Total Chèque + Bank
        line +=1
        count= 0
        cell = column[count]+str(line)
        sheet.write(cell, 'TOTAL CHEQUES + ESPECES', top_column_format)
        count += 3
        cell = column[count]+str(line)
        sheet.write(cell, abs(amount_debit - amount_credit), top_column_format)


        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report_grouping(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format({'font_size': '12px'})
        top_column_format = workbook.add_format({'font_size': '13px', 'bold':True})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'14px'})
        txt = workbook.add_format({'font_size': '10px'})

        sheet.merge_range('A1:G2', "REPARTITION SALLE REGROUPEMENT: "+data['start_date'], head)
        column = XLSX_COLUMN
        top_column = ['Code UE','Nom UE', 'Heure', 'Salle']

        line = 5
        count = 0
        for content in top_column:
            cell = column[count]+str(line)
            sheet.write(cell, content, top_column_format)
            count +=1

        line +=1

        grouping_ids = self.env['regrouping.center'].sudo().search([('date','=', data['start_date'])])
        for line_id in grouping_ids.mapped('regrouping_line_ids'):
            count = 0

            # Code UE
            cell = column[count]+str(line)
            sheet.write(cell, line_id.code_ue, cell_format)

            # Nom UE
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, line_id.ue_config_id.name, cell_format)

            # Heure
            count+=1
            cell = column[count]+str(line)
            begin_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line_id.begin_hours) * 60, 60))
            end_hours = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line_id.end_hours) * 60, 60))
            sheet.write(cell, str(begin_hours)+', '+str(end_hours), cell_format)

            # Salle
            count+=1
            cell = column[count]+str(line)
            str_rooms = ''
            for room in line_id.examen_rooms:
                str_rooms += room.name+',  '
            sheet.write(cell, str_rooms, cell_format)

            line +=1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report_inscription(self, data, response):
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
        column = XLSX_COLUMN
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