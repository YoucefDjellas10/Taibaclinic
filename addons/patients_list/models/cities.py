from odoo import models, fields


class CitiesRecords(models.Model):
    _name = 'cities.records'
    _description = 'Cities Records'

    name = fields.Char(string='Name')
    country = fields.Many2one('country.records', string='Country')

