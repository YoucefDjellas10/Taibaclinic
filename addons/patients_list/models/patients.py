from odoo import fields, models, api
from datetime import date


class Patients(models.Model):
    _name = 'patients'
    _description = 'Patients list'

    name = fields.Char(string='Full name', compute='_compute_full_name', store=True)
    patient_type = fields.Selection([('door', 'Door'),
                                     ('lead', 'Lead'),
                                     ('company', 'Company')], string='Patient Type',
                                     required=True, default='door')
    stage = fields.Selection([('new', 'New Lead'),
                              ('contacted', 'Contacted'),
                              ('not_interested', 'Not interested'),
                              ('qualified', 'Qualified'),
                              ('waiting_details', 'Waiting details'),
                              ('quotation_preparation', 'Quotation preparation'),
                              ('negotiation', 'Negotiation'),
                              ('lost', 'Lost'),
                              ('deal_closed', 'Deal closed'),
                              ('new_beginning', 'New beginning'),
                              ], string='Stage', default='new', tracking=True)
    not_interested_reason = fields.Many2one('not.interested.reason', string='not interested Reason')
    lost_reason_id = fields.Many2one('lost.reason.record', string='lost Reason')
    interested_id = fields.Many2one('interest.record', string='Interest')
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
    note = fields.Text(string='Note')
    payment_total = fields.Monetary(currency_field="currency", string='Total Payments', compute='_compute_payment_total', store=True)
    deal_total = fields.Monetary(currency_field="currency", string='Total Deals', compute='_compute_deal_total', store=True)
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    balance = fields.Monetary(currency_field="currency", string='Balance', compute='_compute_balance', store=True)
    salesperson = fields.Many2one('res.users', string='Salesperson')
    app_total = fields.Monetary(currency_field="currency", string='Total appointments', compute='_compute_app_total_', store=True)

    @api.depends('app_total', 'payment_total')
    def _compute_balance(self):
        for rec in self:
            rec.balance = rec.app_total - rec.payment_total

    @api.depends('appointment_ids.net_total')
    def _compute_app_total_(self):
        for rec in self:
            rec.app_total = sum(rec.appointment_ids.mapped('net_total'))

    @api.depends('deal_ids.net_total')
    def _compute_deal_total(self):
        for rec in self:
            rec.deal_total = sum(rec.deal_ids.mapped('net_total'))

    @api.depends('payment_ids.amount')
    def _compute_payment_total(self):
        for rec in self:
            total = 0.0
            for payment in rec.payment_ids:
                total += payment.amount or 0.0
            rec.payment_total = total

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
            'res_model': 'contact.stage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
            }
        }

    def action_not_interested(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Not interested action',
            'res_model': 'not.interested.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
            }
        }

    def action_lost(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lost action',
            'res_model': 'lost.stage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
            }
        }

    def action_qualified(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'qualified action',
            'res_model': 'qualified.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
                'default_patient': self.id,
            }
        }

    def action_details_received(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Details received',
            'res_model': 'details.received.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
            }
        }

    def action_quotation(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Quotation',
            'res_model': 'quotations.prepare.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_patient_id': self.id,
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

    def action_resend(self):
        self.stage = 'new'

    def action_fix_missing_patient_type(self):
        self.search([('patient_type', '=', False)]).write({'patient_type': 'door'})



