from odoo import models, fields


class LostReasonRecord(models.Model):
    _name = 'lost.reason.record'
    _description = 'lost reason record'

    name = fields.Char(string='Name')
