# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
import json

from odoo import api, fields, models, _
from odoo.exceptions import UserError

DAY_WEEKS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
STATE_UE_VALIDATE = ['account', 'enf', 'accueil']
STATE_ROOM = [
    ('free', 'Libre'),
    ('partially', 'Occupé partiellement'),
    ('busy', 'Occupé')
]

class RegroupingCenter(models.Model):
    _inherit = 'regrouping.center'

    @api.onchange('date')
    def date_change(self):
        for rec in self:
            for line in rec.regrouping_line_ids:
                line.grouping_date = rec.date

    def action_distribution_student(self):
        """Action to distribution """
        self.write({'button_state': 'send'})
        list_assignment = []
        ue_obj = self.env['unit.enseigne']
        assignment_obj = self.env['assignment.student']

        any_room_set =False

        for line in self.regrouping_line_ids:

            # Reset the room and Students to null
            line.write({'examen_rooms': [(6, 0, [])], 'assignement_ids': [(6, 0, [])]})

            domain_ue = [
                ('name', '=', line.ue_config_id.id),
                '|',
                ('inscription_id.school_year', '=', line.regrouping_id.school_year_id.id),
                ('inscription_other_id.school_year', '=', line.regrouping_id.school_year_id.id)
            ]
            ue_ids = ue_obj.search(domain_ue)
            ue_ids = ue_ids.filtered(
                lambda ue: ue.inscription_id.state in STATE_UE_VALIDATE or ue.inscription_other_id.state in STATE_UE_VALIDATE)
            inscription_ids = ue_ids.mapped("inscription_id") + ue_ids.mapped("inscription_other_id")
            students_ids = inscription_ids.mapped("student_id")
            rooms = self.get_avalaible_room(self.date ,line.begin_hours, line.end_hours, line.numbers_student)

            if not rooms:
                break
                # raise UserError(_("Vous n'avez plus aucune salle disponible pour la date et l'heure que vous avez indiqué. Veuillez choisir une nouvelle période pour réessayer."))

            for room in rooms:
                any_room_set = True
                line.write({'examen_rooms': [(4, room.id)]})
                i = 0
                for student in students_ids:
                    if i < room.nb_place:
                        assignment_val = {
                            'student_id': student.id,
                            'regrouping_line_id' : line.id,
                            'room_id': room.id
                        }
                        list_assignment.append(assignment_val)
                        students_ids -= student
                        i += 1
                    else:
                        break

        if list_assignment:
            assignment_obj.create(list_assignment)
        if not any_room_set:
            raise UserError(_("Vous n'avez plus aucune salle disponible pour la date et l'heure que vous avez indiqué. Veuillez choisir une nouvelle période pour réessayer."))

    def get_avalaible_room(self, date, start_time, end_time, numbers):
        # lines = self.env['regrouping.center.line']
        available_room_obj = self.env['examen.room'].sudo()
        not_available_room_id = []
        res_lines = self.env['regrouping.center.line'].sudo().search([('regrouping_id.date', '=', date)])
        for res in res_lines:
            if self.there_is_overlap(start_time, end_time, res.begin_hours,res.end_hours):
                for room in res.examen_rooms:
                    not_available_room_id.append(room.id)

        repartition_exam_ids = self.env['exam.repartition'].sudo().search([('exam_id.date', '=', date)])
        for rep in repartition_exam_ids:
            if self.there_is_overlap(start_time, end_time, rep.exam_id.start_time,rep.exam_id.end_time):
                exam_room = self.env['examen.room'].sudo().search([('name', '=', rep.room)], limit=1)
                not_available_room_id.append(exam_room.id)

        available_room = available_room_obj.search([('id', 'not in', not_available_room_id), ('nb_place_copy', '>=', int(numbers))], order='nb_place_copy ASC', limit=1)
        if available_room:
            return available_room
        else:
            available_rooms = self.env['examen.room'].sudo()
            rooms = available_room_obj.search([('id', 'not in', not_available_room_id), ('nb_place_copy', '<', int(numbers))], order='nb_place_copy DESC')
            reste = int(numbers)
            for room in rooms:
                available_rooms |= room
                reste = reste - int(room.nb_place)
                if reste <= 0:
                    return available_rooms

            if reste >0:
                return False

        return False

    def there_is_overlap(self, nb1,nb2,ch3,ch4):
        return not((nb1 < ch3 and nb2 < ch3) or (nb1 > ch4 and nb2 > ch4))


    def action_envoyer_mail_regroupement(self):
        if self.button_state == 'resend':
            template = self.env.ref("index_custom_cnam.regroupement_re_send_email")
        else:
            self.write({'button_state': 'resend'})
            template = self.env.ref("index_custom_cnam.regroupement_email")
        for line in self.regrouping_line_ids:
            if line.examen_rooms and line.assignement_ids:
                for assignement in line.assignement_ids:
                    if assignement.student_id.email:
                        template_values = {
                            'email_from': 'pounasatu@gmail.com',
                            'email_to': assignement.student_id.email,
                            'email_cc': False,
                            'auto_delete': True,
                            'partner_to': assignement.student_id.id,
                            'scheduled_date': False,
                        }

                        template.write(template_values)
                        context = {
                            'lang': self.env.user.lang,
                            'student_id': assignement.student_id,
                            'room': assignement.room_id,
                            'begin_hours': '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.begin_hours) * 60, 60)),
                            'end_hours': '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line.end_hours) * 60, 60))
                        }
                        with self.env.cr.savepoint():
                            template.with_context(context).send_mail(line.id, force_send=True, raise_exception=True)
                            values = template.generate_email(line.id)
        return True

