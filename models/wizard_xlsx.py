import time
import json
import io
import base64
from datetime import date
from odoo import fields, http, models, _
from odoo.http import request
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

XLSX_COLUMN = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
                'AA','AB','AC','AD','AE','AF','AG','AH','AI','AJ','AK','AL','AM','AN','AO','AP','AQ','AR','AS','AT','AU','AV','AW','AX','AY','AZ',
                'BA','BB','BC','BD','BE','BF','BG','BH','BI','BJ','BK','BL','BM','BN','BO','BP','BQ','BR','BS','BT','BU','BV','BW','BX','BY','BZ',
                'CA','CB','CC','CD','CE','CF','CG','CH','CI','CJ','CK','CL','CM','CN','CO','CP','CQ','CR','CS','CT','CU','CV','CW','CX','CY','CZ',
                'DA','DB','DC','DD','DE','DF','DG','DH','DI','DJ','DK','DL','DM','DN','DO','DP','DQ','DR','DS','DT','DU','DV','DW','DX','DY','DZ',
                'EA','EB','EC','ED','EE','EF','EG','EH','EI','EJ','EK','EL','EM','EN','EO','EP','EQ','ER','ES','ET','EU','EV','EW','EX','EY','EZ']
class AccountBankaStatement(models.Model):
    _inherit = "account.bank.statement"

    def print_xlsx(self):
        report_name = "Relevé_de_caisse.xlsx"
        return {
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': '/xlsx_reports?filename='
                   + (report_name or "")+'&statement_id='+str(self.id)


        
        }   
        

class ExcelWizard(models.TransientModel):
    _name = "example.xlsx.report.wizard"
    start_date = fields.Date(string="Date Début", default=date.today(), required=True)
    end_date = fields.Date(string="Date Fin", default=date.today(), required=False)
    get_model = fields.Char(string="Model", required=False)
    semester_ids = fields.Many2many(string="Semestres", required=False, comodel_name="semestre.edu")
    def print_xlsx(self):
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError('Start Date must be less than End Date')
        tab = ''
        if self.get_model and self.get_model == 'rel_caisse':
            report_name="rel_caisse.xlsx"
        elif self.end_date:
            if self.semester_ids:
                tab = False
                for s in self.semester_ids:
                    if not tab:
                        tab = str(s.id)
                    else:
                        tab = tab +'_'+ str(s.id)
            report_name="Export Inscription "+(str(self.start_date) or '')+"_"+(str(self.end_date) or '')+".xlsx"
        else:
            report_name="Export regroupement "+(str(self.start_date)or '')+".xlsx"
        return {
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': '/xlsx_reports?report_name='
                   + (report_name or "")+'&start_date='+(str(self.start_date) or "")+'&end_date='+(str(self.end_date) or "")+
                   '&get_model='+(str(self.get_model) or "")+'&semester_ids='+(str(tab) or "")+'&filename='+(str(report_name) or "")


        }
    def get_xlsx_report(self, workbook, data):
        if data.get('statement_id'):
            self.get_xlsx_report_caisse_by_statement(workbook, data)
        elif data.get('get_model') and data['get_model'] == 'rel_caisse':
            self.get_xlsx_report_rel_caisse(workbook, data)
        elif data.get('end_date'):
            self.get_xlsx_report_inscription(workbook, data)
        else:
            self.get_xlsx_report_grouping(workbook, data)

    def get_xlsx_report_caisse_by_statement(self, workbook, data):
        sheet = workbook.add_worksheet()

        # column_width
        sheet.set_column('A:A', 11)
        sheet.set_column('B:B', 18)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:K', 14)

        cell_format = workbook.add_format({'font_size': '12px', 'border':True})
        top_column_format = workbook.add_format({'font_size': '12px', 'bold':True,'border':True})
        total_format = workbook.add_format({'font_size': '16px', 'bold':True,'border':True})
        date_format = workbook.add_format({'font_size': '12px', 'bold':True,'align':'center'})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'14px'})
        txt = workbook.add_format({'font_size': '10px'})       

        sheet.merge_range('A1:D4', '', head)

        logo_image = io.BytesIO(base64.b64decode(self.env.company.logo))

        sheet.insert_image('B1', "image.png", {'image_data': logo_image,'x_scale': 0.20,'y_scale':0.20})
        

        statement = self.env['account.bank.statement'].sudo().browse(int(data.get('statement_id')))

        max_rep_stat = self.env['account.bank.statement'].sudo().search([('date', '<',statement.date), ('id', '!=', statement.id),('journal_id', '=', statement.journal_id.id)],order='date DESC',limit=1)

        sheet.merge_range('A6:D7', "JOURNAL DE: "+statement.journal_id.name, head)
        sheet.merge_range('A8:D8', "Date: "+str(statement.date), date_format)
        column = XLSX_COLUMN
        top_column = ['Réference', 'Libellé','Partenaire', 'Débit', 'Crédit']

        line = 9
        count = 0
        for content in top_column:
            cell = column[count]+str(line)
            sheet.write(cell, content, top_column_format)
            count +=1

        line +=1
        amount_debit = 0
        amount_credit = 0

        if max_rep_stat:
            count = 0

            # Réference: Void
            cell = column[count]+str(line)
            sheet.write(cell, '', cell_format)

            # Libellé
            count +=1
            cell = column[count]+str(line)
            sheet.write(cell, 'Report du'+str(max_rep_stat.date), cell_format)

            # Partenaire
            count +=1
            cell = column[count]+str(line)
            sheet.write(cell, '', cell_format)

            # Débit (Les montants Positifs) Crédit (Les montants Négatifs)
            if max_rep_stat.balance_end_real >= 0:
                count+=1
                amount = abs(max_rep_stat.balance_end_real)
                amount_debit += amount
                cell = column[count]+str(line)
                sheet.write(cell, f'{amount:,}', cell_format)
                count+=1
                cell = column[count]+str(line)
                sheet.write(cell, '', cell_format)
            else:
                count += 1
                cell = column[count]+str(line)
                sheet.write(cell, '', cell_format)
                count+=1
                amount = abs(max_rep_stat.balance_end_real)
                amount_credit += amount
                cell = column[count]+str(line)
                sheet.write(cell, f'{amount:,}', cell_format)
            line +=1

        for line_id in statement.mapped('line_ids'):
            count = 0

            # Réference
            cell = column[count]+str(line)
            sheet.write(cell, line_id.ref, cell_format)

            # Libellé
            count +=1
            cell = column[count]+str(line)
            sheet.write(cell, line_id.name, cell_format)

            # Partenaire
            count +=1
            cell = column[count]+str(line)
            if line_id.partner_id:
                partner_name = line_id.partner_id.name
            else:
                partner_name = ''
            sheet.write(cell, partner_name, cell_format)

            # Débit (Les montants Positifs) Crédit (Les montants Négatifs)
            if line_id.amount >= 0:
                count+=1
                amount = abs(line_id.amount)
                amount_debit += amount
                cell = column[count]+str(line)
                sheet.write(cell, f'{amount:,}', cell_format)
                count+=1
                cell = column[count]+str(line)
                sheet.write(cell, '', cell_format)
            else:
                count += 1
                cell = column[count]+str(line)
                sheet.write(cell, '', cell_format)
                count+=1
                amount = abs(line_id.amount)
                amount_credit += amount
                cell = column[count]+str(line)
                sheet.write(cell, f'{amount:,}', cell_format)

            line +=1

        # Total
        count = 0
        cell = column[count]+str(line)
        sheet.write(cell, 'Total', total_format)
        count +=1
        cell = column[count]+str(line)
        sheet.write(cell, '', total_format)
        count +=1
        cell = column[count]+str(line)
        sheet.write(cell, f'{amount_debit:,}', total_format)
        count +=1
        cell = column[count]+str(line)
        sheet.write(cell, f'{amount_credit:,}', total_format)

        # Total Chèque + Bank
        line +=1
        count= 0
        cell = column[count]+str(line)
        sheet.write(cell, '', total_format)
        count +=1
        cell = column[count]+str(line)
        sheet.write(cell, '', total_format)
        count +=1
        cell = column[count]+str(line)
        sheet.write(cell, '', total_format)
        count += 1
        cell = column[count]+str(line)
        sheet.write(cell, f'{abs(amount_debit - amount_credit):,}', total_format)

        if statement.journal_id.type == 'cash':
            # Billetage
            count = 0
            line +=3
            cash_line_ids = statement.cashbox_end_id.cashbox_lines_ids
            merge_cell = 'A'+str(line)+':D'+str(line+1)
            sheet.merge_range(merge_cell, "BILLETAGE", head)
            line +=2
            top_column = ['','Nombre', 'Montant']
            count = 0
            for content in top_column:
                cell = column[count]+str(line)
                sheet.write(cell, content, top_column_format)
                count +=1
            for cash_line_id in cash_line_ids:
                # Void
                line +=1
                count = 0
                cell = column[count]+str(line)
                sheet.write(cell, f'{cash_line_id.coin_value:,}', cell_format)

                # Nombre
                count += 1
                cell = column[count]+str(line)
                sheet.write(cell, str(cash_line_id.number), cell_format)                

                # Amount
                count += 1
                cell = column[count]+str(line)
                sheet.write(cell, f'{cash_line_id.subtotal:,}', cell_format)  

            # Total Cash
            line+=1
            count = 0
            cell = column[count]+str(line)
            sheet.write(cell, 'Total', total_format)
            count += 1
            cell = column[count]+str(line)
            sheet.write(cell, '', total_format)
            count += 1
            cell = column[count]+str(line)
            sheet.write(cell, f'{statement.balance_end_real:,}', total_format) 

    def get_xlsx_report_rel_caisse(self, workbook, data):
        sheet = workbook.add_worksheet()

        sheet.set_column('A:G', 14)

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

    def get_xlsx_report_grouping(self, workbook, data):
        sheet = workbook.add_worksheet()
        
        # column_width
        sheet.set_column('B:E', 15)

        cell_format = workbook.add_format({'font_size': '12px', 'border':True})
        top_column_format = workbook.add_format({'font_size': '13px', 'bold':True,'border': True})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'14px'})
        txt = workbook.add_format({'font_size': '10px'})

        sheet.merge_range('A1:G4', '', head)

        logo_image = io.BytesIO(base64.b64decode(self.env.company.logo))

        sheet.insert_image('D1', "image.png", {'image_data': logo_image,'x_scale': 0.20,'y_scale':0.20})


        sheet.merge_range('A6:G7', "REPARTITION SALLE REGROUPEMENT: "+data['start_date'], head)
        column = XLSX_COLUMN
        top_column = ['Code UE','Nom UE', 'Heure', 'Salle']

        line = 8
        count = 1
        for content in top_column:
            cell = column[count]+str(line)
            sheet.write(cell, content, top_column_format)
            count +=1

        line +=1

        grouping_ids = self.env['regrouping.center'].sudo().search([('date','=', data['start_date'])])
        for line_id in grouping_ids.mapped('regrouping_line_ids'):
            count = 1

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

    def get_xlsx_report_inscription(self, workbook, data):
        sheet = workbook.add_worksheet()
        
        # column_width
        sheet.set_column('A:B', 13)
        sheet.set_column('C:E', 20)
        sheet.set_column('F:G', 13)
        sheet.set_column('H:H', 22)
        sheet.set_column('I:Z', 13)
        cell_format = workbook.add_format({'font_size': '12px', 'border': True})
        top_column_format = workbook.add_format({'font_size': '12px', 'bold':True, 'border': True})
        arrete_format = workbook.add_format({'font_size': '13px', 'bold':True})
        head = workbook.add_format({'align': 'center', 'bold': True,'font_size':'20px'})
        txt = workbook.add_format({'font_size': '10px'})

        sheet.merge_range('A1:K4', '', head)

        logo_image = io.BytesIO(base64.b64decode(self.env.company.logo))

        sheet.insert_image('E1', "image.png", {'image_data': logo_image,'x_scale': 0.20,'y_scale':0.20})

        sheet.merge_range('A5:K6', "INSCRIPTION ET REINSCRIPTION", head)
        column = XLSX_COLUMN
        top_column = ['Auditeur', 'Civilité', 'Nom', 'Nom Marital', 'Prénom', 'Date de naissance', 'Mail', 'Diplôme',
        'UE1','UE2','UE3','UE4','UE5','UE6','UE7','UE8','UE9', 'UE10']
        
        sheet.merge_range('A8:K8', 'Arrêtée le:'+str(date.today()), top_column_format)

        line = 9
        count = 0
        for content in top_column:
            cell = column[count]+str(line)
            sheet.write(cell, content, top_column_format)
            count +=1

        line +=1
        insc_domain = [('date', '>=', data['start_date']), ('date','<=', data['end_date'])]
        inscription_ids = self.env['inscription.edu'].sudo().search(insc_domain)
            
        for insc in inscription_ids:
            semester_insc = insc.get_semester_insc()
            semester_found = False
            if data['semester_ids'] and data['semester_ids'] != 0:
                sem_ids = data['semester_ids'].split('_')
                for sem in semester_insc:
                    if str(sem.id) in sem_ids:
                        semester_found = True
                        break;

                if not semester_found:
                    continue

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
            sheet.write(cell, civilite or '', cell_format)

            # Nom
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.surname or '', cell_format)

            # Nom marital
            count+=1
            cell = column[count]+str(line)
            if insc.name_marital:
                sheet.write(cell, insc.name_marital, cell_format)
            else:
                sheet.write(cell, '', cell_format)
            # Prénom
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.firstname or '', cell_format)

            # Date de naissance
            count+=1
            cell = column[count]+str(line)
            if insc.date_of_birth:
                sheet.write(cell, str(insc.date_of_birth), cell_format)
            else:
                sheet.write(cell, '', cell_format)

            # Mail
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.email or '', cell_format)

            # Diplôme
            count+=1
            cell = column[count]+str(line)
            sheet.write(cell, insc.formation_id.name or '', cell_format)

            # UEs
            for ue in insc.units_enseignes:
                count+=1
                cell = column[count]+str(line)
                sheet.write(cell, ue.name.code or '', cell_format)
            # Other UEs
            for ue in insc.other_ue_ids:
                count+=1
                cell = column[count]+str(line)
                sheet.write(cell, ue.name.code or '', cell_format)
            line +=1