from odoo import models, fields


class InterestRecord(models.Model):
    _name = 'interest.record'
    _description = 'interest list'

    name = fields.Char(string='Name')
