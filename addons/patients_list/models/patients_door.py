from odoo import fields, models, api
from datetime import date


class DoorPatients(models.Model):
    _name = 'door.patients'
    _description = 'For creating patients'

    name = fields.Char(string='Full name', compute='_compute_full_name', store=True)
    patient_type = fields.Selection([('door', 'Door'),
                                     ('lead', 'Lead'),
                                     ('company', 'Compaby')], string='Patient Type', default='door')
    gender = fields.Selection([('Mr', 'Mr'), ('Ms', 'Ms')], string='Gender', required=True)
    first_name = fields.Char(string='First name', required=True)
    last_name = fields.Char(string='Last name', required=True)
    birthday = fields.Date(string='Birthday', required=True)
    email = fields.Char(string='Email', required=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    mobile = fields.Char(string='Mobile', required=True)
    country = fields.Many2one('country.records', string='Country', required=True)
    city = fields.Many2one('cities.records', string='City', required=True)
    medical_histiory = fields.Many2many('medical.history', string='Medical history')

