# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import json
from datetime import datetime
from datetime import timedelta

class ExamRepartition(models.Model):
    _inherit ="exam.repartition"

    inscription_id = fields.Many2one("inscription.edu", string="Inscription")
    def get_exam_center(self):
        for record in self:
            record.center_ids = record.inscription_id.region_center_id

class ConvocationList(models.Model):
    _inherit="convocation.list"

    inscription_id = fields.Many2one("inscription.edu", string="Inscription")

class index_custom_cnam(models.Model):
    _inherit = "exam.calandar"


    calandar_id = fields.Many2one('resource.calendar', 'Calendrier', store=True)

    def get_week_day_of_date(self,date):
        week_day_nb = date.weekday()
        # days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return week_day_nb

    def get_day_period(self, time):
        if time < 12:
            return 'morning'

        return 'afternoon'

    def there_is_overlap(self, nb1,nb2,ch3,ch4):
        return not((nb1 < ch3 and nb2 < ch3) or (nb1 > ch4 and nb2 > ch4))

    def get_available_day(self,day, time_from = 8.0, time_to = 12.0):
        week_day = self.get_week_day_of_date(day) #Return int 0:lundi, 1:mardi,...
        attendance_ok = False
        for attendance in self.calandar_id.attendance_ids:
            dayofweek = attendance.dayofweek
            hour_from = attendance.hour_from
            hour_to = attendance.hour_to
            if (int(week_day) == int(dayofweek)) and (int(time_from) == int(hour_from)) and (int(time_to) == int(hour_to)):
                attendance_ok = True
        if not attendance_ok:
            return False
        for exam in self.exam_ids:
            if (exam.date and exam.start_time and exam.end_time):
                # exam_week_day = self.get_week_day_of_date(exam.date)
                # if(exam.start_time<12):
                #     start_time = 8
                # else:
                #     start_time = 13
                # if (day == exam.date and time_from == start_time):
                #     return False

                if self.there_is_overlap(time_from, time_to, exam.start_time, exam.end_time) and day == exam.date:
                    return False

        return {'date': day, 'start_time': time_from, 'end_time': time_to}


                    
    def recalculate(self):                    
        self.calculate()

    def get_default_start_and_end_time_for_date(self, date, after):
        date_dayofweek = date.weekday() #Return int 0:lundi, 1:mardi,...
        hfrom = False
        hto = False
        for attendance in self.calandar_id.attendance_ids.filtered(lambda at: (int(at.dayofweek) == int(date_dayofweek)) and (float(at.hour_from) > float(after)) ):
            if not hfrom:
                hfrom = attendance.hour_from
                hto = attendance.hour_to
            elif attendance.hour_from < hfrom:
                hfrom = attendance.hour_from
                hto = attendance.hour_to
        return [hfrom, hto]




    def request_available_date(self):
        date_request = self.start_date
        s = 8 #default start_time
        e = 12 #default end_time
        tab_hours_ft = self.get_default_start_and_end_time_for_date(date_request, 6)
        if tab_hours_ft and len(tab_hours_ft) == 2:
            if tab_hours_ft[0]:
                s = tab_hours_ft[0]
            if tab_hours_ft[1]:
                e = tab_hours_ft[1]
        request_date = self.get_available_day(date_request, s, e)
        i = 0
        while(not request_date):
            tab_hours_ft = self.get_default_start_and_end_time_for_date(date_request, e)
            if tab_hours_ft and len(tab_hours_ft) == 2:
                if tab_hours_ft[0]:
                    s = tab_hours_ft[0]
                if tab_hours_ft[1]:
                    e = tab_hours_ft[1]
            if (not tab_hours_ft) or (not tab_hours_ft[0]) or (not tab_hours_ft[1]):
                date_request = date_request+timedelta(1)
                e = 6

            request_date = self.get_available_day(date_request, s, e)

            i += 1
            if i > 200:
                print('_'*100)
                print('No')
                request_date = 'no'
        return request_date


    def calculate(self):
        unit_enseignes_obj = self.env['inscription.edu'].search([('state','in',('enf','accueil','account'))]).mapped('units_enseignes')
        other_ues_obj = self.env['inscription.edu'].search([('state','in',('enf','accueil','account'))]).mapped('other_ue_ids')
        unit_enseignes_obj |= other_ues_obj
        exam_obj = self.env['exam.calandar'].search([('school_year','=',self.school_year.id),
                                                              ('session','=',self.session.id),
                                                              ('semester','=',self.semester.id),
                                                              ('start_date','=',self.start_date)]).mapped('exam_ids')
        for exam in self.exam_ids:
            if not (exam.date and exam.start_time != 0 and exam.end_time != 0):
                dict_date = self.request_available_date()
                if (dict_date != 'no'):
                    exam.sudo().write(dict_date)

            student_list = []
            student_list = self.get_existant_student(exam)
            for unit_enseignes in unit_enseignes_obj:
                inscription_id = unit_enseignes.inscription_id or unit_enseignes.inscription_other_id
                if unit_enseignes.name in exam.ue_ids and exam.centre_ue_id.id==unit_enseignes.center_id.id:
                    student=''
                    if inscription_id.name_marital:
                        student = inscription_id.name_marital
                    if inscription_id.firstname:
                        student = inscription_id.firstname
                    if inscription_id.name_marital and inscription_id.firstname:
                        student = inscription_id.name_marital+inscription_id.firstname

                    if student not in student_list:
                        room_available = self.get_avalaible_room(exam.date, exam.start_time, exam.end_time)
                        place_available = self.get_avalaible_place(room_available, exam.date, exam.start_time, exam.end_time)
                        exam.write({'exam_repartition_ids':[(0,0,{'auditor_number':inscription_id.name, 'student':student, 'room': room_available, 'table': place_available, 'inscription_id': inscription_id.id})]})
                        student_list.append(student)

                        convocation_student = self.env['convocation.list'].sudo().search([('school_year', '=', self.school_year.id), ('inscription_id', '=', inscription_id.id)], limit=1)
                        if convocation_student:
                            convocation_student.write({'line_ids': [(0, 0, {'code':exam.ue_ids_string,'display_name':exam.ue_ids_string,
                                    'date':exam.date,'start_time':exam.start_time,
                                    'end_time':exam.end_time,'room':room_available,'table':place_available})]})
                            exam.write({'convocation_ids': [(4,convocation_student.id)]})
                        else:
                            vals = {
                                'date': self.create_date.date(),
                                'student_id': student,
                                'formation_id': inscription_id.formation_id.id,
                                'auditor_number': inscription_id.name,
                                'address_name': inscription_id.adress,
                                'school_year': self.school_year.id,
                                'exam_ids': [(4, exam.id)],
                                'inscription_id': inscription_id.id,
                                'reg_center_id': inscription_id.region_center_id.id,
                                'line_ids': [(0,0, {'code':exam.ue_code_string,'display_name':exam.ue_ids_string,
                                        'date':exam.date,'start_time':exam.start_time,
                                        'end_time':exam.end_time,'room':room_available,'table':place_available})]
                                }
                            new_convocation = self.env['convocation.list'].create(vals)
                            exam.write({'convocation_ids': [(4,new_convocation.id)]})


    def get_existant_student(self, exam):
        dict_student = []
        for repartition in exam.exam_repartition_ids:
            dict_student.append(repartition.student)

        return dict_student

    def get_avalaible_room(self, date, start_time, end_time):
        room_obj = self.env['examen.room'].search([('state','=','free')])
        for room in room_obj:
            place_dispo = int(room.nb_place)
            occupied = 0
            for exam in self.exam_ids:
                if date == exam.date and self.there_is_overlap(start_time, end_time, exam.start_time,exam.end_time):
                    for repartition in exam.exam_repartition_ids:
                        if room.name == repartition.room:
                            occupied +=1

            if place_dispo > occupied:
                return room.name

        return ''


    def get_avalaible_place(self, room, date, start_time, end_time):
        table_obj = self.env['examen.room'].search([('name','=',room)]).mapped('table_ids')
        for table in table_obj:
            place_dispo = int(table.nb_place)
            occupied = 0
            for exam in self.exam_ids:
                if date == exam.date and self.there_is_overlap(start_time, end_time, exam.start_time,exam.end_time):
                    for repartition in exam.exam_repartition_ids:
                        if table.name == repartition.table:
                            occupied +=1

            if place_dispo > occupied:
                return table.name

        return ''


    def there_is_overlap(self, nb1,nb2,ch3,ch4):
        return not((nb1 < ch3 and nb2 < ch3) or (nb1 > ch4 and nb2 > ch4))

class NoteListFilter(models.Model):
    _inherit = 'note.list.filter'

    def action_generate_note(self):
        inscription_ids = self.env['inscription.edu'].search([('state','in',('enf','accueil','account')),
                                                                 ('school_year','=',self.year.id),
                                                                 ])
        
        for unit_enseignes in inscription_ids.mapped('units_enseignes'):
            if self.unit_enseigne.id == unit_enseignes.name.id and unit_enseignes.center_id.id in self.centre_ids.ids:
                vals={
                    'audit': unit_enseignes.inscription_id.name,
                    'partner_id': unit_enseignes.inscription_id.student_id.id,
                    'name': unit_enseignes.inscription_id.name_marital,
                    'first_name': unit_enseignes.inscription_id.firstname,
                    'date_of_birth': unit_enseignes.inscription_id.date_of_birth,
                    'note_list_filter_id': self.id,
                    'code': unit_enseignes.name.code,
                    'intitule': unit_enseignes.display_name,
                    'unit_enseigne': unit_enseignes.name.id,
                    'centre_ids':[(4,center.id) for center in self.centre_ids],
                    'tutor_id': self.tutor_id.id
                    }
                is_note_obj = self.env['note.list'].search([('audit','=',unit_enseignes.inscription_id.name),
                                                            ('name','=',unit_enseignes.inscription_id.name_marital),
                                                            ('first_name','=',unit_enseignes.inscription_id.firstname),
                                                            ('date_of_birth','=',unit_enseignes.inscription_id.date_of_birth),
                                                            ('note_list_filter_id','=', self.id)])
                if not is_note_obj:
                    self.env['note.list'].create(vals)

        for unit_enseignes in inscription_ids.mapped('other_ue_ids'):
            if self.unit_enseigne.id == unit_enseignes.name.id and unit_enseignes.center_id.id in self.centre_ids.ids:
                vals={
                    'audit': unit_enseignes.inscription_other_id.name,
                    'partner_id': unit_enseignes.inscription_other_id.student_id.id,
                    'name': unit_enseignes.inscription_other_id.name_marital,
                    'first_name': unit_enseignes.inscription_other_id.firstname,
                    'date_of_birth': unit_enseignes.inscription_other_id.date_of_birth,
                    'note_list_filter_id': self.id,
                    'code': unit_enseignes.name.code,
                    'intitule': unit_enseignes.display_name,
                    'unit_enseigne': unit_enseignes.name.id,
                    'centre_ids':[(4,center.id) for center in self.centre_ids],
                    'tutor_id': self.tutor_id.id
                    }
                is_note_obj = self.env['note.list'].search([('audit','=',unit_enseignes.inscription_other_id.name),
                                                            ('name','=',unit_enseignes.inscription_other_id.name_marital),
                                                            ('first_name','=',unit_enseignes.inscription_other_id.firstname),
                                                            ('date_of_birth','=',unit_enseignes.inscription_other_id.date_of_birth),
                                                            ('note_list_filter_id','=', self.id)])
                if not is_note_obj:
                    self.env['note.list'].create(vals)

    def action_generate_sec_session(self):
        # Chef if the exam already has 2nd session générated
        if (self.session.name.find('2') > 0):
            print('*'*100)
            print('This is already 2 session!')
            return 0 
        domain = [('year','=', self.year.id), ('unit_enseigne', '=', self.unit_enseigne.id), ('session.name', 'like', '2'), ('id', '!=', self.id)]
        note_2_session = self.search(domain, limit=1).filtered(lambda n: n.centre_ids == self.centre_ids)
        context = self._context.copy()
        if note_2_session:
            vals = {
                'type': 'ir.actions.act_window',
                'name': note_2_session.session.name,
                'res_model': 'note.list.filter',
                'views': [(self.env.ref('edu_management.view_note_list_filter_tree').id, 'tree'),
                        (self.env.ref('edu_management.view_note_list_filter_form').id, 'form')],
                'context': context,
                'domain': [('id', 'in', note_2_session.ids)],
                'target': 'current',
            }
        else:
            session2 = self.env['sessions.edu'].sudo().search([('name', 'like', '2')], limit=1)
            create_vals = {
                'year': self.year.id,
                'session': session2.id,
                'centre_ids': self.centre_ids.ids,
                'unit_enseigne':self.unit_enseigne.id,
                'tutor_id':self.tutor_id.id,
            }
            new_rec = self.sudo().create(create_vals)
            failed_notes = self.note_list_ids.filtered(lambda nl: nl.mention != 'admis')
            for nt in failed_notes:
                note_failed_vals={
                    'audit': nt.audit,
                    'partner_id': nt.partner_id.id,
                    'name': nt.name,
                    'first_name': nt.first_name,
                    'date_of_birth': nt.date_of_birth,
                    'code': nt.code,
                    'intitule': nt.intitule,
                    'unit_enseigne': nt.unit_enseigne.id,
                    'centre_ids':nt.centre_ids,
                    'tutor_id': nt.tutor_id.id
                }
                new_rec.write({'note_list_ids': [(0,0,note_failed_vals)]})
            vals = {
                'type': 'ir.actions.act_window',
                'name': new_rec.session.name,
                'res_model': 'note.list.filter',
                'views': [(self.env.ref('edu_management.view_note_list_filter_tree').id, 'tree'),
                        (self.env.ref('edu_management.view_note_list_filter_form').id, 'form')],
                'context': context,
                'domain': [('id', '=', new_rec.id)],
                'target': 'current',
            }
        return vals

class NoteList(models.Model):
    _inherit="note.list"

    def get_note_by_student(self, partner_id):
        notes = self.sudo().search([('partner_id', '=', partner_id), ('mention', '=', 'admis')])
        return notes or False
