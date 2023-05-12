# -*- coding: utf-8 -*-

import io
from ast import literal_eval

import xlsxwriter as xlsxwriter

from odoo import http
from odoo.http import request

from datetime import date


class xlsComparisonController(http.Controller):

    @http.route('/web/binary/download_comparison_xls_file', type='http', auth="public")
    def download_comparison_xls_file(self, school_year, semestres=''):  #
        filename = "Liste_comparative.xlsx"
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)

        self.report_excel_xls_comparison(workbook, school_year, semestres)  
        workbook.close()
        output.seek(0)
        xlsheader = [('Content-Type', 'application/octet-stream'),
                     ('Content-Disposition', 'attachment; filename=%s;' % filename)]
        return request.make_response(output, xlsheader)


    def report_excel_xls_comparison(self, workbook, school_year,str_sem):
        worksheet_ost = workbook.add_worksheet("DNS")
        self.style(worksheet_ost)
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
        year_id = request.env['school.year'].sudo().browse(int(school_year))

        year = year_id.name

        school_year_ids = self.get_school_years(year,year_id)

        worksheet_ost.merge_range('C1:G1','TABLEAU DE COMPARAISON - RECAP INSCRIPTION '+str(year),bold_center_11)

        center_ids = request.env['region.center'].sudo().search([])
        row = 4
        for center in center_ids:
            insc_domain = [('region_center_id', '=', center.id), ('type', '=', 'registration')]
            reinsc_domain = [('region_center_id', '=', center.id), ('type', '=', 're-registration')]

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

                insc_ue_ids = insc_ue_ids_temp
                reinsc_ue_ids = reinsc_ue_ids_temp

            if insc_ue_ids or reinsc_ue_ids:
                cell = 'C'+str(row)+':K'+str(row)
                worksheet_ost.merge_range(cell, center.name, cell_bold_center_11)

                row +=1
                if len(school_year_ids)>0:
                    cell = 'C'+str(row)+':E'+str(row)
                    worksheet_ost.merge_range(cell, str(school_year_ids[0][0])+'-'+str(school_year_ids[0][1]), cell_bold_center_11)

                    cell = 'C'+str(row+1)
                    worksheet_ost.write(cell, 'REINS', cell_center_11)
                    cell = 'D'+str(row+1)
                    worksheet_ost.write(cell, 'NVX', cell_center_11)
                    cell = 'E'+str(row+1)
                    worksheet_ost.write(cell, 'UE Vendues', cell_center_11)

                if len(school_year_ids)>1:
                    cell = 'F'+str(row)+':H'+str(row)
                    worksheet_ost.merge_range(cell, str(school_year_ids[1][0])+'-'+str(school_year_ids[1][1]), cell_bold_center_11)

                    cell = 'F'+str(row+1)
                    worksheet_ost.write(cell, 'REINS', cell_center_11)
                    cell = 'G'+str(row+1)
                    worksheet_ost.write(cell, 'NVX', cell_center_11)
                    cell = 'H'+str(row+1)
                    worksheet_ost.write(cell, 'UE Vendues', cell_center_11)

                if len(school_year_ids)>2:
                    cell = 'I'+str(row)+':K'+str(row)
                    worksheet_ost.merge_range(cell, str(school_year_ids[2][0])+'-'+str(school_year_ids[2][1]), cell_bold_center_11)

                    cell = 'I'+str(row+1)
                    worksheet_ost.write(cell, 'REINS', cell_center_11)
                    cell = 'J'+str(row+1)
                    worksheet_ost.write(cell, 'NVX', cell_center_11)
                    cell = 'K'+str(row+1)
                    worksheet_ost.write(cell, 'UE Vendues', cell_center_11)


                self.fillDateCell(worksheet_ost, row +1, cell_bold_center_11)
                self.fillUeData(worksheet_ost, row+2, cell_center_11,school_year_ids,reinsc_ue_ids, insc_ue_ids)

                row += 104

    def fillUeData(self, worksheet_ost, row, row_style, year_ids, reinsc_ids, insc_ids):
        counter = 0
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
            for m in month_tab_1:
                if m in [9,11]:
                    day_tab = [(1,7), (8,15), (16,22), (23,30)]
                else:
                    day_tab = [(1,7), (8,15), (16,22), (23,31)]

                for day in day_tab:
                    date_begin = date(int(year_tab[0]), m, day[0])
                    date_end = date(int(year_tab[0]), m, day[1])
                    reinsc_filtered = reinsc_ids.filtered(lambda re: re.date >= date_begin and re.date <= date_end)
                    insc_filtered = insc_ids.filtered(lambda insc: insc.date >= date_begin and insc.date <= date_end)
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
                elif m == 2:
                    day_tab = [(1,7), (8,15), (16,22), (23,28)]
                else:
                    day_tab = [(1,7), (8,15), (16,22), (23,31)]

                for day in day_tab:
                    date_begin = date(int(year_tab[1]), m, day[0])
                    date_end = date(int(year_tab[1]), m, day[1])
                    reinsc_filtered = reinsc_ids.filtered(lambda re: re.date >= date_begin and re.date <= date_end)
                    insc_filtered = insc_ids.filtered(lambda insc: insc.date >= date_begin and insc.date <= date_end)
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


    def fillDateCell(self,worksheet_ost, row, row_style):
        cell = 'A'+str(row)
        worksheet_ost.write(cell, 'MOIS', row_style)
        cell = 'B'+str(row)
        worksheet_ost.write(cell, 'DATE', row_style)

        months = ['JUILLET', 'AOUT', 'SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DECEMBRE', 'JANVIER', 'FEVRIER','MARS', 'AVRIL', 'MAI','JUIN']

        row += 1

        for month in months:
            cell = 'A'+str(row)+':A'+str(row+7)
            worksheet_ost.merge_range(cell, month, row_style)

            cell = 'B'+str(row)+':B'+str(row+1)
            worksheet_ost.merge_range(cell, "01er Au 07",row_style)
            cell = 'B'+str(row+2)+':B'+str(row+3)
            worksheet_ost.merge_range(cell, "08 Au 15",row_style)
            cell = 'B'+str(row+4)+':B'+str(row+5)
            worksheet_ost.merge_range(cell, "16 Au 22",row_style)
            cell = 'B'+str(row+6)+':B'+str(row+7)
            worksheet_ost.merge_range(cell, "23 Au 30",row_style)

            row += 8
        cell = 'A'+str(row)+':B'+str(row+1)
        worksheet_ost.merge_range(cell, 'TOTAL', row_style)


    def style(self, worksheet):
        worksheet.set_column('A:A', 17)
        worksheet.set_column('B:B', 13)
        worksheet.set_column('C:K', 11)
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

