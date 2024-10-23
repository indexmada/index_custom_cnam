# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import json
from datetime import datetime

SELECTION_STATE = [
    ('pre-inscription', 'Pré-inscription'),
    ('accueil', 'Validé Acceuil'),
    ('account', 'Validé comptable'),
    ('enf', 'Validé ENF'),
    ('cancel', 'Annulé')
]

class index_custom_cnam(models.Model):
    _inherit = "regrouping.center.line"

    name = fields.Char("Nom", compute="compute_line_name")

    def _set_default_grouping_date(self):
        return self.regrouping_id.date

    begin_hours = fields.Float("Heure de début", required=True)
    end_hours = fields.Float("Heure de Fin", required=True)

    begin_date_time = fields.Datetime("Date et Heure de début", compute='_compute_begin_date_time')
    end_date_time = fields.Datetime("Date et Heure de fin", compute='_compute_end_date_time')
    school_year_id = fields.Many2one("school.year", "Année Universitaire", required=True, compute='compute_school_year')
    grouping_date = fields.Date("Date du regroupement", store=True, default=_set_default_grouping_date)

    student_pointed_ids = fields.Many2many("assignment.student", "regrouping_line_id", string="Pointage", domain="[('id', 'in', assignement_ids)]")

    @api.onchange('code_ue', 'assignement_ids', 'duration')
    def _set_d_grouping_date(self):
        for record in self:
            record.grouping_date = record.regrouping_id.date

    def compute_school_year(self):
        for line in self:
            line.school_year_id = line.regrouping_id.school_year_id

    def _compute_begin_date_time(self):
        for line in self:
            begin_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.begin_hours) * 60, 60))
            begin_time = datetime.strptime(begin_time.replace(':', ''), '%H%M').time()
            if begin_time and line.regrouping_id.date:
                line.begin_date_time = datetime.combine(line.regrouping_id.date, begin_time)
            else:
                line.begin_date_time = None

    def _compute_end_date_time(self):
        for line in self:
            end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.end_hours) * 60, 60))
            end_time = datetime.strptime(end_time.replace(':', ''), '%H%M').time()
            if end_time and line.regrouping_id.date:
                line.end_date_time = datetime.combine(line.regrouping_id.date, end_time)
            else:
                line.end_date_time = None

    @api.depends("begin_hours", "end_hours")
    def compute_duration(self):
        for line in self:
            duration = line.end_hours - line.begin_hours
            if duration < 0:
                line.duration = 0
            else:
                line.duration = duration

    def compute_line_name(self):
        for line in self:
            line.name = str(line.code_ue) + ' ' + str(line.school_year_id.name)

    def _get_regrouping_line_by_ue(self, ue_config_id, school_year_id):
        regrouping_lines = self.sudo().search([('ue_config_id', '=', int(ue_config_id)), ('regrouping_id.school_year_id', '=', school_year_id)], order="grouping_date ASC")
        return regrouping_lines

    def _get_grouping_date_dayofweek(self):
        date = self.grouping_date
        dayofweek = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        nb_jours = date.weekday()
        return dayofweek[nb_jours]


class RegroupingCentre(models.Model):
    _inherit = "regrouping.center"

    reg_date_begin = fields.Datetime("Heure de début du regroupement", compute="compute_reg_date_begin")
    reg_date_end = fields.Datetime("Heure de fin du regroupement", compute="compute_reg_date_end")

    @api.depends("reg_date_begin")
    def compute_reg_date_begin(self):
        for reg in self:
            min = 23.5
            for line in reg.regrouping_line_ids:
                if min > line.begin_hours:
                    min = line.begin_hours
            min = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(min) * 60, 60))
            min_time = datetime.strptime(min.replace(':', ''), '%H%M').time()
            reg.reg_date_begin = datetime.combine(reg.date, min_time)

    @api.depends("reg_date_end")
    def compute_reg_date_end(self):
        for reg in self:
            max = 0
            for line in reg.regrouping_line_ids:
                if max < line.end_hours:
                    max = line.end_hours
            max = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(max) * 60, 60))
            max_time = datetime.strptime(max.replace(':', ''), '%H%M').time()
            reg.reg_date_end = datetime.combine(reg.date, max_time)

    def get_all_line(self):
        for regroup in self:
            result = []
            for line in regroup.regrouping_line_ids:
                dict_line = {
                    'day_of_week': line.day_of_week,
                    'date': str(regroup.date),
                    'begin_hours': str(line.begin_hours),
                    'end_hours': str(line.end_hours),
                    'duration': line.duration
                }
                result.append(dict_line)
            regroup.lines_JSON = json.dumps(result) if result else False


class ExamRoom(models.Model):
    _inherit = "examen.room"

    def compute_state(self):
        now = fields.Datetime.now()
        for room in self:
            regrouping = room.regrouping_lines_ids.filtered(lambda grouping: grouping.begin_date_time and grouping.end_date_time and grouping.begin_date_time <= now <= grouping.end_date_time)
            if regrouping:
                room.state = 'busy' if regrouping.numbers_student > 0 else 'partially'
            else:
                room.state = 'free'


class Year(models.Model):
    _name = "year.year"

    name = fields.Integer("Année")


class UnitEnseignementConfig(models.Model):
    _inherit = 'unit.enseigne.config'

    def _get_default_formation_ids(self):
        for record in self:
            record.formation_ids = record.formation_id

    formation_ids = fields.Many2many("training.edu", string="Formations", default=_get_default_formation_ids)
    years = fields.Many2many("year.year", string="Années")
    same_exam_room = fields.Boolean("Même Salle d'examen", default=False)

    def merge_ue(self):
        same_ue_ids = self.search([('code', '=', self.code)])
        formation_ids = same_ue_ids.mapped('formation_id')
        for formation in formation_ids:
            if formation not in self.formation_ids:
                self.write({'formation_ids': [(4, formation.id)]})

        years = same_ue_ids.mapped('year')
        for year in years:
            year_id = self.env['year.year'].sudo().search([('name', '=', year)])
            if year_id and year_id not in self.years:
                self.write({'years': [(4, year_id.id)]})

        for ue in same_ue_ids:
            exam_ids = self.env['exam.exam'].sudo().search([]).filtered(lambda x: ue in x.ue_ids)
            for exam in exam_ids:
                if ue in exam.ue_ids and ue != self:
                    exam.write({'ue_ids': [(3, ue.id)]})
                    exam.write({"ue_ids": [(4, self.id)]})

        insc_ue_id = self.env['unit.enseigne'].sudo().search([('name.id', 'in', same_ue_ids.mapped("id")), ('name.id', '!=', self.id)])
        for ue_id in insc_ue_id:
            ue_id.write({'name': self.id})

        note_ids = self.env['note.list'].sudo().search([('unit_enseigne', 'in', same_ue_ids.ids), ('unit_enseigne', '!=', self.id)])
        for note in note_ids:
            note.write({"unit_enseigne": self.id})

        note_list_filter_ids = self.env['note.list.filter'].sudo().search([('unit_enseigne', 'in', same_ue_ids.ids), ('unit_enseigne', '!=', self.id)])
        for note_list in note_list_filter_ids:
            note_list.write({"unit_enseigne": self.id})

        reg_ids = self.env['regrouping.center.line'].sudo().search([('ue_config_id', 'in', same_ue_ids.ids), ('ue_config_id', '!=', self.id)])
        for reg in reg_ids:
            reg.write({"ue_config_id": self.id})

        for unit_enseigne in same_ue_ids:
            if unit_enseigne != self:
                unit_enseigne.unlink()


class InscriptionEducation(models.Model):
    _inherit = "inscription.edu"

    def get_semester_insc(self):
        semester_ids = self.env['semestre.edu'].sudo()
        for ue in self
