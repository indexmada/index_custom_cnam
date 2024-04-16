# -*- coding: utf-8 -*-

import io
from ast import literal_eval

import base64
import xlsxwriter as xlsxwriter

from odoo import http
from odoo.http import request

from datetime import date

UE_CENTER_NAME = ['MADAGASCAR', 'REUNION']

class xlsComparisonController(http.Controller):

    @http.route('/web/binary/download_comparison_xls_file', type='http', auth="public")
    def download_comparison_xls_file(self, school_year, semestres='', display_by='', center_id_str=""):  #
        filename = "Liste_comparative.xlsx"
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        center_ids = False
        if center_id_str and display_by == "organisatrice":
            center_tab = center_id_str.split("-")
            center_ids = request.env["examen.center"].sudo().search([('id', 'in', [eval(i) for i in center_tab])])

        self.report_excel_xls_comparison(workbook, school_year, semestres, display_by, center_ids)  
        workbook.close()
        output.seek(0)
        xlsheader = [('Content-Type', 'application/octet-stream'),
                     ('Content-Disposition', 'attachment; filename=%s;' % filename)]
        return request.make_response(output, xlsheader)


    def report_excel_xls_comparison(self, workbook, school_year,str_sem, display, req_center_ids):
        tab = ['monthly', 'weekly']
        bold_center_11 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            "font_size": 11,
            'bold': True,
        })
        cell_bold_center_11 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'top': 1,
            'left': 1,
            'right': 1,
            'bottom': 1,
            'right_color': 'black',
            'bottom_color': 'black',
            'top_color': 'black',
            'left_color': 'black',
            "font_size": 11,
            "bold": True,
        })
        cell_center_11 = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'top': 1,
            'left': 1,
            'right': 1,
            'bottom': 1,
            'right_color': 'black',
            'bottom_color': 'black',
            'top_color': 'black',
            'left_color': 'black',
            "font_size": 11,
            "bold": False
        })
        row_tab = ["A", "B", "C", "D", "E", "F", "G", "H", "I", 'J', 'K', 'L', "M", "N", "O", "P"]
        for t in tab:
            sheet_name = "Par mois" if t == "monthly" else "Par Semaine"
            worksheet_ost = workbook.add_worksheet(sheet_name)
            if t == 'monthly':
                self.style_month(worksheet_ost)
            else:
                self.style(worksheet_ost)

            year_id = request.env['school.year'].sudo().browse(int(school_year))

            year = year_id.name

            school_year_ids = self.get_school_years(year,year_id)

            worksheet_ost.merge_range('B1:G1','TABLEAU DE COMPARAISON - RECAP INSCRIPTION '+str(year),bold_center_11)

            center_domain = [("id", 'in', req_center_ids.ids)] if req_center_ids else []

            center_ids = request.env['region.center'].sudo().search(center_domain) if display == 'exam' else request.env['examen.center'].sudo().search(center_domain)
            row = 4
            for center in center_ids:
                if display == 'exam':
                    insc_domain = [('region_center_id', '=', center.id), ('type', '=', 'registration')]
                    reinsc_domain = [('region_center_id', '=', center.id), ('type', '=', 're-registration')]
                else:
                    # insc_domain = [('type', '=', 'registration')]
                    # reinsc_domain = [('type', '=', 're-registration')]
                    insc_domain = [('examen_center_id', '=', center.id), ('type', '=', 'registration')]
                    reinsc_domain = [('examen_center_id', '=', center.id), ('type', '=', 're-registration')]

                insc_ue_ids = request.env['inscription.edu'].sudo().search(insc_domain)
                reinsc_ue_ids = request.env['inscription.edu'].sudo().search(reinsc_domain)

                insc_ue_ids_temp = request.env['inscription.edu'].sudo()
                reinsc_ue_ids_temp = request.env['inscription.edu'].sudo()

                if str_sem and str_sem != '':
                    sem_ids = str_sem.split('-')
                    for i in sem_ids:
                        # for insc in insc_ue_ids:
                        #     print('*'*20)
                        #     print(i,' ---- ', insc.get_semester_insc().ids)
                        insc_ue_ids_temp |= insc_ue_ids.filtered(lambda insc: int(i) in insc.get_semester_insc().ids)
                        reinsc_ue_ids_temp |= reinsc_ue_ids.filtered(lambda re: int(i) in re.get_semester_insc().ids)

                    # if display != 'exam':
                    #     reinsc_ue_ids_temp = reinsc_ue_ids_temp.filtered(lambda x: center in (x.units_enseignes+x.other_ue_ids).mapped('center_id'))
                    #     insc_ue_ids_temp = insc_ue_ids_temp.filtered(lambda x: center in (x.units_enseignes+x.other_ue_ids).mapped('center_id'))

                    insc_ue_ids = insc_ue_ids_temp
                    reinsc_ue_ids = reinsc_ue_ids_temp

                if insc_ue_ids or reinsc_ue_ids:
                    col1 = 1 if t == "monthly" else 2
                    col2 = 9 if t == "monthly" else 10
                    cell = row_tab[col1]+str(row)+':'+row_tab[col2]+str(row)
                    worksheet_ost.merge_range(cell, center.name, cell_bold_center_11)

                    row +=1
                    if len(school_year_ids)>0:
                        cell = row_tab[col1]+str(row)+':'+row_tab[col1+2]+str(row)
                        worksheet_ost.merge_range(cell, str(school_year_ids[0][0])+'-'+str(school_year_ids[0][1]), cell_bold_center_11)

                        cell = row_tab[col1]+str(row+1)
                        worksheet_ost.write(cell, 'REINS', cell_center_11)
                        cell = row_tab[col1+1]+str(row+1)
                        worksheet_ost.write(cell, 'NVX', cell_center_11)
                        cell = row_tab[col1+2]+str(row+1)
                        worksheet_ost.write(cell, 'UE Vendues', cell_center_11)

                    if len(school_year_ids)>1:
                        cell = row_tab[col1+3]+str(row)+':'+row_tab[col1+5]+str(row)
                        worksheet_ost.merge_range(cell, str(school_year_ids[1][0])+'-'+str(school_year_ids[1][1]), cell_bold_center_11)

                        cell = row_tab[col1+3]+str(row+1)
                        worksheet_ost.write(cell, 'REINS', cell_center_11)
                        cell = row_tab[col1+4]+str(row+1)
                        worksheet_ost.write(cell, 'NVX', cell_center_11)
                        cell = row_tab[col1+5]+str(row+1)
                        worksheet_ost.write(cell, 'UE Vendues', cell_center_11)

                    if len(school_year_ids)>2:
                        cell = row_tab[col1+6]+str(row)+':'+row_tab[col1+8]+str(row)
                        worksheet_ost.merge_range(cell, str(school_year_ids[2][0])+'-'+str(school_year_ids[2][1]), cell_bold_center_11)

                        cell = row_tab[col1+6]+str(row+1)
                        worksheet_ost.write(cell, 'REINS', cell_center_11)
                        cell = row_tab[col1+7]+str(row+1)
                        worksheet_ost.write(cell, 'NVX', cell_center_11)
                        cell = row_tab[col1+8]+str(row+1)
                        worksheet_ost.write(cell, 'UE Vendues', cell_center_11)

                    monthly = True if t == "monthly" else False

                    self.fillDateCell(worksheet_ost, row +1, cell_bold_center_11, monthly)
                    self.fillUeData(worksheet_ost, row+2, cell_center_11,school_year_ids,reinsc_ue_ids, insc_ue_ids, monthly, center, display)

                    if t == "monthly":
                        row += 32
                    else:
                        row += 104

    def fillUeData(self, worksheet_ost, row, row_style, year_ids, reinsc_ids, insc_ids, monthly, center, display):
        counter = 0
        if monthly:
            col = ["B", "E", "H"]
            col_nvx = ["C", "F", "I"]
            col_ue = ["D", "G", "J"]

        else:
            col = ['C', 'F', 'I']
            col_nvx = ['D', 'G', 'J']
            col_ue = ['E', 'H', 'K']

        for year_id in year_ids:
            year_tab = year_id
            month_tab_1 = [7,8,9,10,11,12]
            month_tab_2 = [1,2,3,4,5,6]
            r = row
            total_reinsc = 0
            total_insc = 0
            total_ue = 0
            school_year_ids = self.env['school.year'].sudo().search([]).filtered(lambda x: x.name.find(year_tab[0]) >= 0 and x.name.find(year_tab[1]) >= 0)
            
            if school_year_ids and len(school_year_ids):
                school_year_id = school_year_ids[0]
            else:
                school_year_id = 'XYZ'

            for m in month_tab_1:
                if m in [9,11]:
                    day_tab = [(1,7), (8,15), (16,22), (23,30)]
                    month_end = 30
                else:
                    day_tab = [(1,7), (8,15), (16,22), (23,31)]
                    month_end = 31
                if monthly:
                    date_begin = date(int(year_tab[0]), m, 1)
                    date_end = date(int(year_tab[0]), m, month_end)
                    reinsc_filtered = reinsc_ids.filtered(lambda re: re.date >= date_begin and re.date <= date_end and re.school_year == school_year_id)
                    insc_filtered = insc_ids.filtered(lambda insc: insc.date >= date_begin and insc.date <= date_end and insc.school_year == school_year_id)

                    cell = col[counter]+str(r)
                    cell_nvx = col_nvx[counter]+str(r)
                    worksheet_ost.write(cell, len(reinsc_filtered), row_style)
                    worksheet_ost.write(cell_nvx, len(insc_filtered), row_style)

                    cell_tot = col[counter]+str(r+1)+':'+col_nvx[counter]+str(r+1)
                    worksheet_ost.merge_range(cell_tot, len(reinsc_filtered)+len(insc_filtered), row_style)

                    # UE Vendues
                    # if display == "exam":
                    #     nb_ue = len(reinsc_filtered.mapped('units_enseignes')) + len(reinsc_filtered.mapped('other_ue_ids')) + len(insc_filtered.mapped('units_enseignes')) + len(insc_filtered.mapped('other_ue_ids'))

                    # else:
                    #     all_insc = reinsc_filtered +insc_filtered
                    #     all_ue_ids = all_insc.mapped('units_enseignes') + all_insc.mapped('other_ue_ids')
                    #     all_ue_filtered = all_ue_ids.filtered(lambda x: x.center_id == center)
                    #     nb_ue = len(all_ue_filtered)

                    nb_ue = len(reinsc_filtered.mapped('units_enseignes')) + len(reinsc_filtered.mapped('other_ue_ids')) + len(insc_filtered.mapped('units_enseignes')) + len(insc_filtered.mapped('other_ue_ids'))

                    cell_ue = col_ue[counter]+str(r)+':'+col_ue[counter]+str(r+1)
                    worksheet_ost.merge_range(cell_ue, str(nb_ue), row_style)

                    # Increase Total
                    total_reinsc += len(reinsc_filtered)
                    total_insc += len(insc_filtered)
                    total_ue += nb_ue

                    r+= 2
                else:
                    for day in day_tab:
                        date_begin = date(int(year_tab[0]), m, day[0])
                        date_end = date(int(year_tab[0]), m, day[1])
                        reinsc_filtered = reinsc_ids.filtered(lambda re: re.date >= date_begin and re.date <= date_end and re.school_year == school_year_id)
                        insc_filtered = insc_ids.filtered(lambda insc: insc.date >= date_begin and insc.date <= date_end and insc.school_year == school_year_id)
                        cell = col[counter]+str(r)
                        cell_nvx = col_nvx[counter]+str(r)
                        worksheet_ost.write(cell, len(reinsc_filtered), row_style)
                        worksheet_ost.write(cell_nvx, len(insc_filtered), row_style)

                        cell_tot = col[counter]+str(r+1)+':'+col_nvx[counter]+str(r+1)
                        worksheet_ost.merge_range(cell_tot, len(reinsc_filtered)+len(insc_filtered), row_style)

                        # UE Vendues
                        nb_ue = len(reinsc_filtered.mapped('units_enseignes')) + len(reinsc_filtered.mapped('other_ue_ids')) + len(insc_filtered.mapped('units_enseignes')) + len(insc_filtered.mapped('other_ue_ids'))
                        cell_ue = col_ue[counter]+str(r)+':'+col_ue[counter]+str(r+1)
                        worksheet_ost.merge_range(cell_ue, str(nb_ue), row_style)

                        # Increase Total
                        total_reinsc += len(reinsc_filtered)
                        total_insc += len(insc_filtered)
                        total_ue += nb_ue

                        r+= 2

            for m in month_tab_2:
                if m in [4,6]:
                    day_tab = [(1,7), (8,15), (16,22), (23,30)]
                    month_end = 30
                elif m == 2:
                    day_tab = [(1,7), (8,15), (16,22), (23,28)]
                    month_end = 28
                else:
                    day_tab = [(1,7), (8,15), (16,22), (23,31)]
                    month_end = 31

                if monthly: 
                    date_begin = date(int(year_tab[1]), m, 1)
                    date_end = date(int(year_tab[1]), m, month_end)
                    reinsc_filtered = reinsc_ids.filtered(lambda re: re.date >= date_begin and re.date <= date_end and re.school_year == school_year_id)
                    insc_filtered = insc_ids.filtered(lambda insc: insc.date >= date_begin and insc.date <= date_end and insc.school_year == school_year_id)
                    cell = col[counter]+str(r)
                    cell_nvx = col_nvx[counter]+str(r)
                    worksheet_ost.write(cell, len(reinsc_filtered), row_style)
                    worksheet_ost.write(cell_nvx, len(insc_filtered), row_style)

                    cell_tot = col[counter]+str(r+1)+':'+col_nvx[counter]+str(r+1)
                    worksheet_ost.merge_range(cell_tot, len(reinsc_filtered)+len(insc_filtered), row_style)

                    # UE Vendues
                    nb_ue = len(reinsc_filtered.mapped('units_enseignes')) + len(reinsc_filtered.mapped('other_ue_ids')) + len(insc_filtered.mapped('units_enseignes')) + len(insc_filtered.mapped('other_ue_ids'))
                    cell_ue = col_ue[counter]+str(r)+':'+col_ue[counter]+str(r+1)
                    worksheet_ost.merge_range(cell_ue, str(nb_ue), row_style)

                    # Increase Total
                    total_reinsc += len(reinsc_filtered)
                    total_insc += len(insc_filtered)
                    total_ue += nb_ue

                    r+= 2

                else:
                    for day in day_tab:
                        date_begin = date(int(year_tab[1]), m, day[0])
                        date_end = date(int(year_tab[1]), m, day[1])
                        reinsc_filtered = reinsc_ids.filtered(lambda re: re.date >= date_begin and re.date <= date_end and re.school_year == school_year_id)
                        insc_filtered = insc_ids.filtered(lambda insc: insc.date >= date_begin and insc.date <= date_end and insc.school_year == school_year_id)
                        cell = col[counter]+str(r)
                        cell_nvx = col_nvx[counter]+str(r)
                        worksheet_ost.write(cell, len(reinsc_filtered), row_style)
                        worksheet_ost.write(cell_nvx, len(insc_filtered), row_style)

                        cell_tot = col[counter]+str(r+1)+':'+col_nvx[counter]+str(r+1)
                        worksheet_ost.merge_range(cell_tot, len(reinsc_filtered)+len(insc_filtered), row_style)

                        # UE Vendues
                        nb_ue = len(reinsc_filtered.mapped('units_enseignes')) + len(reinsc_filtered.mapped('other_ue_ids')) + len(insc_filtered.mapped('units_enseignes')) + len(insc_filtered.mapped('other_ue_ids'))
                        cell_ue = col_ue[counter]+str(r)+':'+col_ue[counter]+str(r+1)
                        worksheet_ost.merge_range(cell_ue, str(nb_ue), row_style)

                        # Increase Total
                        total_reinsc += len(reinsc_filtered)
                        total_insc += len(insc_filtered)
                        total_ue += nb_ue

                        r+= 2

            # Total
            # Reinsc
            cell = col[counter]+str(r)
            worksheet_ost.write(cell, total_reinsc,row_style)

            # Insc
            cell = col_nvx[counter]+str(r)
            worksheet_ost.write(cell, total_insc,row_style)

            # Reinsc + Insc
            cell = col[counter]+str(r+1)+':'+col_nvx[counter]+str(r+1)
            worksheet_ost.merge_range(cell, total_reinsc + total_insc, row_style)

            # Ue
            cell = col_ue[counter]+str(r)+':'+col_ue[counter]+str(r+1)
            worksheet_ost.merge_range(cell, total_ue,row_style)

            counter +=1


    def fillDateCell(self,worksheet_ost, row, row_style, monthly = False):
        cell = 'A'+str(row)
        worksheet_ost.write(cell, 'MOIS', row_style)
        if not monthly:
            cell = 'B'+str(row)
            worksheet_ost.write(cell, 'DATE', row_style)

        months = ['JUILLET', 'AOUT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DECEMBRE', 'JANVIER', 'FEVRIER','MARS', 'AVRIL', 'MAI','JUIN']

        row += 1

        for month in months:
            if monthly:
                cell = 'A'+str(row)+':A'+str(row+1)
            else:
                cell = 'A'+str(row)+':A'+str(row+7)
            worksheet_ost.merge_range(cell, month, row_style)

            if monthly:
                row += 2
            else:
                cell = 'B'+str(row)+':B'+str(row+1)
                worksheet_ost.merge_range(cell, "01er Au 07",row_style)
                cell = 'B'+str(row+2)+':B'+str(row+3)
                worksheet_ost.merge_range(cell, "08 Au 15",row_style)
                cell = 'B'+str(row+4)+':B'+str(row+5)
                worksheet_ost.merge_range(cell, "16 Au 22",row_style)
                cell = 'B'+str(row+6)+':B'+str(row+7)
                worksheet_ost.merge_range(cell, "23 Au 30",row_style)

                row += 8
        if monthly:
            cell = 'A'+str(row)+':A'+str(row+1)
        else:
            cell = 'A'+str(row)+':B'+str(row+1)
        worksheet_ost.merge_range(cell, 'TOTAL', row_style)


    def style(self, worksheet):
        worksheet.set_column('A:A', 17)
        worksheet.set_column('B:B', 13)
        worksheet.set_column('C:K', 11)
        for i in range(1,300):
            worksheet.set_row(i, 18)

    def style_month(self, worksheet):
        worksheet.set_column('A:A', 17)
        worksheet.set_column('B:K', 11)
        for i in range(1,300):
            worksheet.set_row(i, 18)

    def get_school_years(self, year_name, year_id):
        year_tab = year_name.split('-')
        year1 = int(year_tab[0]) -1
        year2 = int(year_tab[1]) -1
        year3 = year1 -1
        year4 = year2 -1
        # school_ids = request.env['school.year'].sudo().search([('name','like', year3), ('name', 'like', year4)])
        # school_ids |= request.env['school.year'].sudo().search([('name','like', year1), ('name', 'like', year2)])
        # school_ids |= year_id
        school_ids = [(year3, year4), (year1, year2), (year_tab[0], year_tab[1])]
        return school_ids

class InscriptionEdu(http.Controller):

    @http.route('/navette_export', type='http', auth="public")
    def download_navette_file(self, file_name, id_tab=''):  #
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        self.report_excel_navette(workbook, id_tab)  
        workbook.close()
        output.seek(0)
        xlsheader = [('Content-Type', 'application/octet-stream'),
                     ('Content-Disposition', 'attachment; filename=%s;' % file_name)]
        return request.make_response(output, xlsheader)

    def report_excel_navette(self, workbook, id_tab):
        id_tab = id_tab.split('_')
        for i in id_tab:
            ins = request.env['inscription.edu'].sudo().browse(int(i))
            if not ins:
                continue

            sheet_name = str(ins.id)+" - "+ ins.display_name
            print("_"*100)
            print(sheet_name)
            worksheet_ost = workbook.add_worksheet(sheet_name)
            self.style(worksheet_ost)

            cell_bold_center_11 = workbook.add_format({
                'align': 'center',
                'valign': 'vcenter',
                'top': 1,
                'left': 1,
                'right': 1,
                'bottom': 1,
                'right_color': 'black',
                'bottom_color': 'black',
                'top_color': 'black',
                'left_color': 'black',
                "font_size": 11,
                "bold": True,
            })
            right_10 = workbook.add_format({
                'align': 'right',
                'valign': 'vright',
                "font_size": 10,
                "bold": False,
            })
            left_10 = workbook.add_format({
                'align': 'left',
                'valign': 'vleft',
                "font_size": 10,
                "bold": False,
            })

            bold_10_center = workbook.add_format({
                "align": "center",
                "valign": "vcenter",
                "font_size": 10,
                "bold": True,
                })

            bold_10_left = workbook.add_format({
                "align": "left",
                "valign": "vleft",
                "font_size": 10,
                "bold": True,
                })

            center_12 = workbook.add_format({
                "align": "center",
                "valign": "vcenter",
                "font_size": 12,
                "bold": False,
                })
            cell_10_center = workbook.add_format({
                "align": "center",
                "valign": "vcenter",
                "font_size": 10,
                "bold": False,
                'top': 1,
                'left': 1,
                'right': 1,
                'bottom': 1,
                'right_color': 'black',
                'bottom_color': 'black',
                'top_color': 'black',
                'left_color': 'black',
                })

            cell_10_center_bold = workbook.add_format({
                "align": "center",
                "valign": "vcenter",
                "font_size": 10,
                "bold": True,
                'top': 1,
                'left': 1,
                'right': 1,
                'bottom': 1,
                'right_color': 'black',
                'bottom_color': 'black',
                'top_color': 'black',
                'left_color': 'black',
                })

            cell_10_left = workbook.add_format({
                "align": "left",
                "valign": "vleft",
                "font_size": 10,
                "bold": False,
                'top': 1,
                'left': 1,
                'right': 1,
                'bottom': 1,
                'right_color': 'black',
                'bottom_color': 'black',
                'top_color': 'black',
                'left_color': 'black',
                })

            logo_image = io.BytesIO(base64.b64decode(request.env.company.logo))
            worksheet_ost.insert_image('A1', "image.png", {'image_data': logo_image,'x_scale': 0.60,'y_scale':0.60})

            dtoday = date.today()

            today = "Le "+str(dtoday.day)+'/'+str(dtoday.month)+'/'+str(dtoday.year)+" à Antananarivo"
            worksheet_ost.merge_range("E1:F1", today, right_10)

            worksheet_ost.write("E3", "Centre régional inscripteur :", right_10)
            worksheet_ost.write("F3", "Madagascar", left_10)
            worksheet_ost.write("E7", "Région organisatrice:", right_10)
            worksheet_ost.write("F7", ins.examen_center_id.name or '', left_10)
            worksheet_ost.write("E8", "Centre régional correspondant: ", right_10)
            worksheet_ost.write("F8", ins.examen_center_id.name or '', left_10)
            worksheet_ost.write("E9", "Fax: ", right_10)
            worksheet_ost.write("A10", "Année: "+ins.school_year.name if ins.school_year else '', left_10)
            worksheet_ost.write("A11", "Contact: ", left_10)
            worksheet_ost.write("A12", "Jocelyn RASOANAIVO ", left_10)
            worksheet_ost.write("A13", "261 20 22 290 19", left_10)
            worksheet_ost.write("A14", "cnam.madagascar@yahoo.com", left_10)
            worksheet_ost.merge_range("A18:F18", "Inscription pédagogique en formation ouverte à distance (FOD)", bold_10_center)
            worksheet_ost.merge_range("A19:F19", "au Centre d'enseignement d'Antananarivo", bold_10_center)
            worksheet_ost.write("A23", "Nous vous prions de trouver ci-joint l'inscription de: ", left_10)
            worksheet_ost.write("B24", "Civilité:", bold_10_left)
            civilite = "Monsieur" if ins.civilite == "mr" else "Madame" if ins.civilite == "mme" else "Mademoiselle"
            worksheet_ost.write("D24", civilite, left_10)
            worksheet_ost.write("B25", "Nom patronymique: ", bold_10_left)
            worksheet_ost.write("D25", ins.surname or '', left_10)
            worksheet_ost.write("B26", "Nom marital: ", bold_10_left)
            worksheet_ost.write("D26", ins.name_marital or '', left_10)
            worksheet_ost.write("B27", "Prénoms: ", bold_10_left)
            worksheet_ost.write("D27", ins.firstname or '', left_10)
            worksheet_ost.write("B28", "Notre numéro d'auditeur(trice):", bold_10_left)
            worksheet_ost.write("E28", ins.name or '', left_10)
            worksheet_ost.write("A30", "auditeur(trice) du Centre d'enseignement d'Antananarivo, à des formations à distance organisées par votre centre régional ", left_10)
            worksheet_ost.write("B32", "Né(e) Le: ", bold_10_left)
            dnaiss = ins.date_of_birth
            dnaiss_format = str(dnaiss.day)+"/"+str(dnaiss.month)+"/"+str(dnaiss.year)
            worksheet_ost.write("C32", dnaiss_format or '', center_12)
            worksheet_ost.write("E32", "à: "+ins.place_of_birth, left_10)
            worksheet_ost.write("B33", "Adresse", bold_10_left)
            worksheet_ost.write("C33", ins.adress or '', left_10)
            worksheet_ost.write("B34", "Adresse 2", bold_10_left)
            worksheet_ost.write("B35", "CP", bold_10_left)
            worksheet_ost.write("C35", ins.zip or '', left_10)
            worksheet_ost.write("E35", "Ville: "+(ins.student_id.city or ''), left_10)
            worksheet_ost.write("B36", "Mail", bold_10_left)
            worksheet_ost.write("C36", ins.email or '', left_10)
            worksheet_ost.write("B37", "Tél: ", bold_10_left)
            worksheet_ost.write("C37", ins.phone or '', left_10)
            worksheet_ost.write("E37", "Portable: "+(ins.mobile or ''), left_10)


            worksheet_ost.write("A39", "DATE INSCRIPTION", cell_10_center_bold)
            worksheet_ost.write("B39", "Notre réf.", cell_10_center_bold)
            worksheet_ost.write("C39", "CODE UE", cell_10_center_bold)
            worksheet_ost.write("D39", "SEMESTRE", cell_10_center_bold)
            worksheet_ost.write("E39", "INTITULE", cell_10_center_bold)
            worksheet_ost.write("F39", "ECTS", cell_10_center_bold)

            ue_ids = ins.units_enseignes + ins.other_ue_ids
            line = 40
            for ue in ue_ids.filtered(lambda x: x.center_id and x.center_id.name.upper() not in UE_CENTER_NAME):
                cell = "A"+str(line)
                worksheet_ost.write(cell, ins.inscription_date.strftime("%d/%m/%Y") if ins.inscription_date else '', cell_10_center)
                cell = "B"+str(line)
                worksheet_ost.write(cell, '', cell_10_center)
                cell = "C"+str(line)
                worksheet_ost.write(cell, ue.name.code or '', cell_10_center)
                cell = "D"+str(line)
                worksheet_ost.write(cell, ue.semestre_id.name or '', cell_10_center)
                cell = "E"+str(line)
                worksheet_ost.write(cell, ue.name.name or '', cell_10_center)
                cell = "F"+str(line)
                worksheet_ost.write(cell, ue.name.ects or '', cell_10_center)
                line += 1

            line += 1
            cell = "E"+str(line)
            worksheet_ost.write(cell, "Confirmation", bold_10_left)
            line += 1
            cell = "E"+str(line)
            worksheet_ost.write(cell, "(Visa du centre organisateur)", bold_10_left)
            line += 1
            cell = "E"+str(line)
            worksheet_ost.write(cell, "", workbook.add_format({'left': 1, 'left_color': 'black', 'top': 1, 'top_color': 'black'}))
            cell = "F"+str(line)
            worksheet_ost.write(cell, "", workbook.add_format({'right': 1, 'right_color': 'black', 'top': 1, 'top_color': 'black'}))
            
            line +=1
            for temp in range(0,3):
                cell = "E"+str(line)
                worksheet_ost.write(cell, "", workbook.add_format({'left': 1, 'left_color': 'black'}))
                cell = "F"+str(line)
                worksheet_ost.write(cell, "", workbook.add_format({'right': 1, 'right_color': 'black'}))
                line += 1

            cell = "E"+str(line)
            worksheet_ost.write(cell, "", workbook.add_format({'left': 1, 'left_color': 'black', 'bottom': 1, 'bottom_color': 'black'}))
            cell = "F"+str(line)
            worksheet_ost.write(cell, "", workbook.add_format({'right': 1, 'right_color': 'black', 'bottom': 1, 'bottom_color': 'black'}))

            line += 1
            cell = "A"+str(line)
            worksheet_ost.write(cell, "Les droits seront acquités et l'inscription effective dès confirmation de votre part auprès du centre d'Antananarivo  ", left_10)

    def style(self, worksheet):
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:D', 10)
        worksheet.set_column('E:E', 24)
        worksheet.set_column('F:F', 18)