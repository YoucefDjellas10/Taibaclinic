from odoo import models, fields


class CountryRecords(models.Model):
    _name = 'country.records'
    _description = 'Country Records'

    name = fields.Char(string='Name')

