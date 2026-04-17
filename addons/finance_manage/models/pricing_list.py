from odoo import models, fields


class PricingList(models.Model):
    _name = "pricing.list"
    _description = "pricing list of all treatment"
    _rec_name = "treatment"

    name = fields.Char(string="Name")
    treatment = fields.Many2one('treatments', string='treatments', required=True)
    currency = fields.Many2one('res.currency',
                               string='Currency', required=True,
                               default=lambda self: self.env.ref('base.DZD'))
    min_price = fields.Monetary(currency_field='currency', string='Min price', required=True)
    default_price = fields.Monetary(currency_field='currency', string='Default price', required=True)
    category = fields.Many2one('price.category', string='category', required=True)
    note = fields.Text(string='Note')
