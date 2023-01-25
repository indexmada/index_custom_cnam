# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import json
from datetime import datetime
from datetime import timedelta

class ExamRepartition(models.Model):
    _inherit ="exam.repartition"

    inscription_id = fields.Many2one("inscription.edu", string="Inscription")

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

    def get_available_day(self,day, time_from = 8.0, time_to = 12.0):
        print('*'*100)
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
                exam_week_day = self.get_week_day_of_date(exam.date)
                if(exam.start_time<12):
                    start_time = 8
                else:
                    start_time = 13
                if (day == exam.date and time_from == start_time):
                    return False
        return {'date': day, 'start_time': time_from, 'end_time': time_to}


                    
    def recalculate(self):                    
        self.calculate()

    def request_available_date(self):
        date_request = self.start_date
        s = 8 #default start_time
        e = 12 #default end_time
        request_date = self.get_available_day(date_request, s, e)
        i = 0
        while(not request_date):
            if s == 8:
                s = 13
                e = 17
            else:
                s = 8
                e = 12
                date_request = date_request+timedelta(1)

            request_date = self.get_available_day(date_request, s, e)

            i += 1
            if i > 100:
                request_date = 'no'
        return request_date


    def calculate(self):
        unit_enseignes_obj = self.env['inscription.edu'].search([('state','in',('enf','accueil','account'))]).mapped('units_enseignes')
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
                if unit_enseignes.name in exam.ue_ids and exam.centre_ue_id.id==unit_enseignes.center_id.id:
                    student=''
                    if unit_enseignes.inscription_id.name_marital:
                        student = unit_enseignes.inscription_id.name_marital
                    if unit_enseignes.inscription_id.firstname:
                        student = unit_enseignes.inscription_id.firstname
                    if unit_enseignes.inscription_id.name_marital and unit_enseignes.inscription_id.firstname:
                        student = unit_enseignes.inscription_id.name_marital+unit_enseignes.inscription_id.firstname

                    if student not in student_list:
                        room_available = self.get_avalaible_room(exam.date, exam.start_time, exam.end_time)
                        place_available = self.get_avalaible_place(room_available, exam.date, exam.start_time, exam.end_time)
                        exam.write({'exam_repartition_ids':[(0,0,{'auditor_number':unit_enseignes.inscription_id.name, 'student':student, 'room': room_available, 'table': place_available, 'inscription_id': unit_enseignes.inscription_id.id})]})
                        student_list.append(student)

                        convocation_student = self.env['convocation.list'].sudo().search([('school_year', '=', self.school_year.id), ('inscription_id', '=', unit_enseignes.inscription_id.id)], limit=1)
                        if convocation_student:
                            convocation_student.write({'line_ids': [(0, 0, {'code':exam.ue_ids_string,'display_name':exam.ue_ids_string,
                                    'date':exam.date,'start_time':exam.start_time,
                                    'end_time':exam.end_time,'room':room_available,'table':place_available})]})
                            exam.write({'convocation_ids': [(4,convocation_student.id)]})
                        else:
                            vals = {
                                'date': self.create_date.date(),
                                'student_id': student,
                                'formation_id': unit_enseignes.inscription_id.formation_id.id,
                                'auditor_number': unit_enseignes.inscription_id.name,
                                'address_name': unit_enseignes.inscription_id.adress,
                                'school_year': self.school_year.id,
                                'exam_ids': [(4, exam.id)],
                                'inscription_id': unit_enseignes.inscription_id.id,
                                'line_ids': [(0,0, {'code':exam.ue_ids_string,'display_name':exam.ue_ids_string,
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


                
    