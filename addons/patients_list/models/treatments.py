from odoo import fields, models


class Treatments(models.Model):
    _name = 'treatments'
    _description = 'treatments'

    name = fields.Char(string='Treatment name')
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    price = fields.Monetary(string='Price', currency_field='currency')
