from odoo import fields, models


class PatientAttachments(models.Model):
    _name = 'patient.attachments'
    _description = 'All attachments for patients'

    name = fields.Char(string='Name')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    patient = fields.Many2one('patients', string='Patient')


