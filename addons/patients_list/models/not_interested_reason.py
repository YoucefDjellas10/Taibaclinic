from odoo import fields, models


class NotInterestedReason(models.Model):
    _name = 'not.interested.reason'
    _description = 'not interested reason'

    name = fields.Char(string='Name')
