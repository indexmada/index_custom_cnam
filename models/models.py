# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import json
from datetime import datetime


class index_custom_cnam(models.Model):
    _inherit = "regrouping.center.line"

    name = fields.Char("Nom", compute="compute_line_name")

    begin_hours = fields.Float("Heure de début", required=True)
    end_hours = fields.Float("Heure de Fin", required=True)

    begin_date_time = fields.Datetime("Date et Heure de début", compute='_compute_begin_date_time')
    end_date_time = fields.Datetime("Date et Heure de fin", compute='_compute_end_date_time')
    school_year_id = fields.Many2one("school.year", "Année Universitaire", required=True,compute='compute_school_year')

    def compute_school_year(self):
        for line in self:
            line.school_year_id = line.regrouping_id.school_year_id

    def _compute_begin_date_time(self):
        for line in self:
            begin_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.begin_hours) * 60, 60))
            begin_time = datetime.strptime(begin_time.replace(':', ''),'%H%M').time()
            line.begin_date_time =  datetime.combine(line.regrouping_id.date, begin_time)
            print('*'*50)
            print(line.begin_date_time)

    def _compute_end_date_time(self):
        for line in self:
            end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.end_hours) * 60, 60))
            end_time = datetime.strptime(end_time.replace(':', ''),'%H%M').time()
            line.end_date_time = datetime.combine(line.regrouping_id.date, end_time)

    @api.depends("begin_hours", "end_hours")
    def compute_duration(self):
        """Compute duration regrouping"""
        for line in self:
            duration = line.end_hours - line.begin_hours
            if duration < 0:
                line.duration = 0
            else:
                line.duration = duration

    def compute_line_name(self):
        for line in self:
            line.name = str(line.code_ue)+' '+str(line.school_year_id.name)

class RegroupingCentre(models.Model):
    _inherit = "regrouping.center"

    reg_date_begin = fields.Datetime("Heure de début du regroupement", compute="compute_reg_date_begin")
    reg_date_end = fields.Datetime("Heure du fin du regroupement", compute="compute_reg_date_end")

    @api.depends("reg_date_begin")
    def compute_reg_date_begin(self):
        for reg in self:
            min = 100
            for line in reg.regrouping_line_ids:
                if min > line.begin_hours:
                    min = line.begin_hours
            min = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(min) * 60, 60))
            min_time = datetime.strptime(min.replace(':', ''),'%H%M').time()
            reg.reg_date_begin = datetime.combine(reg.date, min_time)

    @api.depends("reg_date_end")
    def compute_reg_date_end(self):
        for reg in self:
            max = 0
            for line in reg.regrouping_line_ids:
                if max < line.end_hours:
                    max = line.end_hours
            max = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(max) * 60, 60))
            max_time = datetime.strptime(max.replace(':', ''),'%H%M').time()
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
        """Get state Room"""
        now = fields.Datetime.now()
        for room in self:
            regrouping = room.regrouping_lines_ids.filtered(lambda grouping: grouping.begin_date_time <= now <= grouping.end_date_time)
            if regrouping:
                room.state = 'occuped' if regrouping.numbers_student > 0 else 'partially'
            else:
                room.state = 'free'

