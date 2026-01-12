from odoo import fields, models, api
from datetime import date


class Doctors(models.Model):
    _name = 'doctors'
    _description = 'Doctors list'

    name = fields.Char(string='Full name', compute='_compute_full_name', store=True)
    account = fields.Many2one('res.users', string='Account', required=True)
    speciality = fields.Many2one('doctor.speciality', string='Speciality')
    gender = fields.Selection([('Mr', 'Mr'), ('Ms', 'Ms')], string='Gender', required=True)
    first_name = fields.Char(string='First name', required=True)
    last_name = fields.Char(string='Last name', required=True)
    birthday = fields.Date(string='Birthday', required=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    mobile = fields.Char(string='Mobile', required=True)

    @api.depends('birthday')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            if rec.birthday:
                rec.age = today.year - rec.birthday.year - (
                        (today.month, today.day) < (rec.birthday.month, rec.birthday.day)
                )
            else:
                rec.age = 0

    @api.depends('gender', 'first_name', 'last_name')
    def _compute_full_name(self):
        for rec in self:
            parts = []
            if rec.gender:
                parts.append(rec.gender)
            if rec.first_name:
                parts.append(rec.first_name)
            if rec.last_name:
                parts.append(rec.last_name)

            rec.name = " ".join(parts)
