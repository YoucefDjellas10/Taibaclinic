from odoo import fields,models


class LaboratoryList(models.Model):
    _name = 'laboratory.list'
    _description = 'laboratory list'

    name = fields.Char(string='Name')
