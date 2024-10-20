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
    school_year_id = fields.Many2one("school.year", "Année Universitaire", required=True, compute='compute_school_year', store=True)
    grouping_date = fields.Date("Date du regroupement", store=True, default=_set_default_grouping_date)

    student_pointed_ids = fields.Many2many("assignment.student", "regrouping_line_id", string="Pointage", domain="[('id', 'in', assignement_ids)]")

    # def _get_grouping_date(self):
    #     for record in self:
    #         record.grouping_date = record.regrouping_id.date
    @api.onchange('code_ue','assignement_ids','duration')
    def _set_d_grouping_date(self):
        for record in self:
            record.grouping_date = record.regrouping_id.date

    def compute_school_year(self):
        for line in self:
            line.school_year_id = line.regrouping_id.school_year_id

    def _compute_begin_date_time(self):
        for line in self:
            begin_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.begin_hours) * 60, 60))
            begin_time = datetime.strptime(begin_time.replace(':', ''),'%H%M').time()
            if begin_time and line.regrouping_id.date:
                line.begin_date_time =  datetime.combine(line.regrouping_id.date, begin_time)
            else:
                line.begin_date_time = None
            print('*'*50)
            print(line.begin_date_time)

    def _compute_end_date_time(self):
        for line in self:
            end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.end_hours) * 60, 60))
            end_time = datetime.strptime(end_time.replace(':', ''),'%H%M').time()
            if end_time and line.regrouping_id.date:
                line.end_date_time = datetime.combine(line.regrouping_id.date, end_time)
            else:
                line.end_date_time = None

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

    def _get_regrouping_line_by_ue(self, ue_config_id,school_year_id):
        print('_'*100)
        print(school_year_id)
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
    reg_date_end = fields.Datetime("Heure du fin du regroupement", compute="compute_reg_date_end")

    @api.depends("reg_date_begin")
    def compute_reg_date_begin(self):
        for reg in self:
            min = 23.5
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
            regrouping = room.regrouping_lines_ids.filtered(lambda grouping: grouping.begin_date_time and grouping.end_date_time and grouping.begin_date_time <= now <= grouping.end_date_time)
            if regrouping:
                room.state = 'busy' if regrouping.numbers_student > 0 else 'partially'
            else:
                room.state = 'free'

class Year(models.Model):
    _name="year.year"

    name = fields.Integer("Année")


class UnitEnseignementConfig(models.Model):
    _inherit = 'unit.enseigne.config'

    def _get_default_formation_ids(self):
        for record in self:
            record.formation_ids = record.formation_id

    formation_ids = fields.Many2many("training.edu", string="Formations", default=_get_default_formation_ids)
    years = fields.Many2many("year.year", string="Années")
    same_exam_room = fields.Boolean("Même Salle d'examen", default = False)
    
    def merge_ue(self):
        print('*'*100)
        print('Merging ue..............')
        print(self.code)
        print(self.name)
        # Merge Formation
        same_ue_ids = self.search([('code', '=', self.code)])
        formation_ids = same_ue_ids.mapped('formation_id')
        for formation in formation_ids:
            if formation not in self.formation_ids:
                self.write({'formation_ids': [(4, formation.id)]})

        # Merge Year
        years = same_ue_ids.mapped('year')
        for year in years:
            year_id = self.env['year.year'].sudo().search([('name', '=', year)])
            if year_id and year_id not in self.years:
                self.write({'years':[(4, year_id.id)]})

        print('Merge Finished')

        # Update the field ue of the exam. 
        for ue in same_ue_ids:
            exam_ids = self.env['exam.exam'].sudo().search([]).filtered(lambda x: ue in x.ue_ids)

            for exam in exam_ids:
                if ue in exam.ue_ids and ue != self:
                    exam.write({'ue_ids': [(3, ue.id)]})
                    exam.write({"ue_ids": [(4, self.id)]})

        # Update the field ue of the Unité d'enseignement and Autre UE dans Inscription
        insc_ue_id = self.env['unit.enseigne'].sudo().search([('name.id', 'in', same_ue_ids.mapped("id")), ('name.id', '!=', self.id)])
        for ue_id in insc_ue_id:
            ue_id.write({'name': self.id})

        # Update UE field in note
        note_ids = self.env['note.list'].sudo().search([('unit_enseigne', 'in', same_ue_ids.ids), ('unit_enseigne', '!=', self.id)])
        for note in note_ids:
            note.write({"unit_enseigne": self.id})

        # Update UE field in note_list_filter
        note_list_filter_ids = self.env['note.list.filter'].sudo().search([('unit_enseigne', 'in', same_ue_ids.ids), ('unit_enseigne', '!=', self.id)])
        for note_list in note_list_filter_ids:
            note_list.write({"unit_enseigne": self.id})


        # Update UE field in regrouping
        reg_ids = self.env['regrouping.center.line'].sudo().search([('ue_config_id', 'in', same_ue_ids.ids), ('ue_config_id', '!=', self.id)])
        for reg in reg_ids:
            reg.write({"ue_config_id": self.id})

        for unit_enseigne in same_ue_ids:
            if unit_enseigne != self:
                unit_enseigne.unlink()


class InscriptionEducation(models.Model):
    _inherit="inscription.edu"

    def get_semester_insc(self):
            semester_ids = self.env['semestre.edu'].sudo()
            for ue in self.units_enseignes:
                if ue.semestre_id:
                    semester_ids |= ue.semestre_id
            for other in self.other_ue_ids:
                if other.semestre_id:
                    semester_ids |= other.semestre_id
            return semester_ids

    @api.depends("surname", "name_marital", "firstname")
    def compute_display_name(self):
        for insc in self:
            # insc.display_name = "%s %s %s" % (insc.surname, insc.name_marital, insc.firstname)
            display_name = ''
            if insc.surname:
                display_name += insc.surname+' '
            if insc.name_marital:
                display_name += insc.name_marital+' '
            if insc.firstname:
                display_name += insc.firstname
            insc.display_name = display_name

    def export_fiche_navette(self):
        report_name = "fiche_navette.xlsx"
        id_tab = False
        for i in self:
            if not id_tab:
                id_tab = str(i.id)
            else:
                id_tab += "_"+str(i.id)
        if not id_tab:
            id_tab=""
        return {
            'type': 'ir.actions.act_url',
            'target': 'current',
            'url': '/navette_export?file_name='
                   + (report_name or "")+'&id_tab='+id_tab        
        }  

    def action_regenerate_num_audit(self):
        for rec in self:
            # num_audit = rec.generate_num_auditeur()
            insc = True
            while(insc):
                num_audit = rec.generate_num_auditeur()
                insc = self.env['inscription.edu'].sudo().search([('name', '=', num_audit)])
            rec.write({'name': num_audit})

class UEReport(models.Model):
    _inherit = "unit.enseigne"

    @api.model
    def default_insc_date_stored(self):
        for record in self:
            print('#...'*20)
            print('here')
            if record.inscription_id:
                record.insc_date_stored = record.inscription_id.inscription_date
            elif record.inscription_other_id:
                record.insc_date_stored = record.inscription_other_id.inscription_date
            else:
                print('none: ', record.id)
                record.insc_date_stored = None

    @api.model
    def default_insc_state(self):
        for record in self:
            print('*'*100) 
            print('here')
            if record.inscription_id:
                record.inscri_state = record.inscription_id.state
            elif record.inscription_other_id:
                record.inscri_state = record.inscription_other_id.state



    insc_date = fields.Date("Date d'inscription(non-storable)", compute="compute_insc_date")
    insc_date_stored = fields.Date("Date d'inscription", default=default_insc_date_stored, compute="get_insc_date_stored", store=True)
    global_insc = fields.Many2one("inscription.edu", string="Etudiant", compute="get_global_insc")
    inscri_state = fields.Selection(SELECTION_STATE, string="Statut", compute="get_insc_state", default=default_insc_state, store=True)
    n_auditeur = fields.Char("Numéro auditeur", compute="get_n_auditeur")

    email = fields.Char("Email", compute="compute_val")
    exam_center = fields.Many2one("region.center", string="Centre d'examen", compute="compute_val")

    def compute_val(self):
        for rec in self:
            global_insc = rec.inscription_id or rec.inscription_other_id
            if global_insc:
                rec.email = global_insc.email
                rec.exam_center = global_insc.region_center_id

    def get_n_auditeur(self):
        for record in self:
            record.n_auditeur = record.global_insc.name

    def get_global_insc(self):
        for record in self:
            record.global_insc = record.inscription_id or record.inscription_other_id

    def compute_insc_date(self):
        for record in self:
            record.insc_date = record.inscription_id.date or record.inscription_other_id.date

    @api.depends("inscription_id", "inscription_other_id", "inscription_id.state", "inscription_other_id.state")
    def get_insc_state(self):
        for record in self:
            if record.inscription_id:
                record.inscri_state = record.inscription_id.state
            elif record.inscription_other_id:
                record.inscri_state = record.inscription_other_id.state

    @api.depends("inscription_id", "inscription_other_id", "inscription_id.inscription_date", "inscription_other_id.inscription_date")
    def get_insc_date_stored(self):
        for record in self:
            print('#...'*20)
            print('here')
            if record.inscription_id:
                record.insc_date_stored = record.inscription_id.inscription_date
            elif record.inscription_other_id:
                record.insc_date_stored = record.inscription_other_id.inscription_date
            else:
                print('none: ', record.id)
                record.insc_date_stored = None
