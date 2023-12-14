# -*- coding: utf-8 -*-

from odoo import models, fields, api

class XlsComparison(models.Model):
    _name = "xls.comparison"
    _description = "Tableau de comparaison Inscription"

    school_year = fields.Many2one(string="Années Universitaire", comodel_name="school.year")
    semester_ids = fields.Many2many(string="Semestres", comodel_name="semestre.edu")
    display_by = fields.Selection(string="Afficher Par", selection=[('exam', "Centre d'examen"), ("organisatrice", "Centre organisatrice")])

    def generate_report(self):
        school_year = str(self.school_year.id)
        str_semester = ''
        for semester in self.semester_ids:
            if str_semester and str_semester != '':
                str_semester += '-'+str(semester.id)
            else:
                str_semester = str(semester.id)
        actions = {
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': '/web/binary/download_comparison_xls_file?school_year='
                   + school_year+'&semestres='+str_semester+'&display_by='+ self.display_by
        }
        return actions