# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import json
from datetime import datetime


class index_custom_cnam(models.Model):
    _inherit = "regrouping.center.line"

    begin_hours = fields.Float("Heure de début", required=True)
    end_hours = fields.Float("Heure de Fin", required=True)

    @api.depends("begin_hours", "end_hours")
    def compute_duration(self):
        """Compute duration regrouping"""
        for line in self:
            line.duration = line.end_hours - line.begin_hours

class RegroupingCentre(models.Model):
    _inherit = "regrouping.center"

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

    def convert_Float_to_time(time_float):
        result = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(time_float) * 60, 60))
        return result

    def compute_state(self):
        """Get state Room"""
        now = fields.Datetime.now()
        for room in self:
            # regrouping = room.regrouping_lines_ids.filtered(lambda grouping: self.convert_Float_to_time(grouping.begin_hours) <= now.strftime("%H:%M") <= self.convert_Float_to_time(grouping.end_hours))
            if False:
                room.state = 'occuped' if regrouping.numbers_student > 0 else 'partially'
            else:
                room.state = 'free'

