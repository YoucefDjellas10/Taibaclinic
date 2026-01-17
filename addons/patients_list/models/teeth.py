from odoo import fields, models


class Teeth(models.Model):
    _name = 'teeth'
    _description = 'teeth'

    name = fields.Char(string='tooth number')
    description = fields.Char(string='Description')
