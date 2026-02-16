from odoo import fields, models, api
from datetime import date


class Patients(models.Model):
    _name = 'patients'
    _description = 'Patients list'

    name = fields.Char(string='Full name', compute='_compute_full_name', store=True)
    patient_type = fields.Selection([('door', 'Door'),
                                     ('lead', 'Lead'),
                                     ('company', 'Compaby')], string='Patient Type')
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
    quotation_ids = fields.One2many('quotations', 'patient', string='Quotations')
    deal_ids = fields.One2many('treatment.plan', 'patient', string='Deals')
    attachment_ids = fields.One2many('patient.attachments', 'patient', string='attachments')
    payment_ids = fields.One2many('patient.payment', 'patient', string='Payments')

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

    def action_add_contact(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Contact',
            'res_model': 'contact.record',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient': self.id,
            }
        }

    def action_add_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Attachment',
            'res_model': 'patient.attachments',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient': self.id,
            }
        }

    def action_add_quotations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Quotation',
            'res_model': 'quotations',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient': self.id,
            }
        }

    def action_add_appointments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Appointment',
            'res_model': 'appointment.record',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient': self.id,
            }
        }

    def action_add_deals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Deal',
            'res_model': 'treatment.plan',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient': self.id,
            }
        }

    def action_add_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Payment',
            'res_model': 'patient.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient': self.id,
            }
        }



