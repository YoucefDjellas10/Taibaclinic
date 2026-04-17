from odoo import models, fields


class PriceCategory(models.Model):
    _name = "price.category"
    _description = "Price category"

    name = fields.Char(string="Name")
