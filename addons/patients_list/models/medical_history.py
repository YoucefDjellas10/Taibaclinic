from odoo import fields, models, api


class MedicalHistory(models.Model):
    _name = 'medical.history'
    _description = 'Medical history of patients'

    name = fields.Char(string='Name')
