# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import json
from datetime import datetime


class index_custom_cnam(models.Model):
    _inherit = "exam.calandar"


    calandar_id = fields.Many2one('resource.calendar', 'Calendrier', store=True)
