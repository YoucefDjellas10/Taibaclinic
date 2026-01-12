from odoo import fields, models


class DoctorSpeciality(models.Model):
    _name = 'doctor.speciality'
    _description = 'Doctor Speciality'

    name = fields.Char(string='Speciality', required=True)
    description = fields.Text(string='Description')
