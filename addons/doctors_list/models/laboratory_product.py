from odoo import fields,models


class LaboratoryProduct(models.Model):
    _name = 'laboratory.product'
    _description = 'laboratory product list'

    name = fields.Char(string='Name')

