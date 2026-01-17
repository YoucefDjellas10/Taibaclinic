from odoo import fields, models, api
from datetime import date


class Patients(models.Model):
    _name = 'patients'
    _description = 'Patients list'

    name = fields.Char(string='Full name', compute='_compute_full_name', store=True)
    stage = fields.Selection([('new', 'New Lead'),
                              ('contacted', 'Contacted'),
                              ('qualified', 'Qualified'),
                              ('consult_booked', 'Consultation Booked'),
                              ('consult_done', 'Consultation Done'),
                              ('plan_sent', 'Treatment Plan Sent'),
                              ('pending', 'Decision Pending'),
                              ('approved', 'Approved'),
                              ('deposit', 'Deposit Paid'),
                              ('scheduled', 'Treatment Scheduled'),
                              ('in_treatment', 'In Treatment'),
                              ('completed', 'Treatment Completed'),
                              ('followup', 'Follow-up'),
                              ('closed', 'Closed'),
                              ], string='Stage', default='new', tracking=True)
    gender = fields.Selection([('Mr', 'Mr'), ('Ms', 'Ms')], string='Gender', required=True)
    first_name = fields.Char(string='First name', required=True)
    last_name = fields.Char(string='Last name', required=True)
    birthday = fields.Date(string='Birthday', required=True)
    email = fields.Char(string='Email', required=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    mobile = fields.Char(string='Mobile', required=True)
    country = fields.Many2one('country.records', string='Country', required=True)
    city = fields.Many2one('cities.records', string='City', required=True)
    appointment_ids = fields.One2many('appointment.record', 'patient', string='Appointments')
    contact_ids = fields.One2many('contact.record', 'patient', string='Contacts')
    medical_histiory = fields.Many2many('medical.history', string='Medical history')

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
