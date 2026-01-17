from odoo import fields, models, api
from dateutil.relativedelta import relativedelta


class Quotations(models.Model):
    _name = 'quotations'
    _description = 'quotations for patients'

    name = fields.Char(string='ID', readonly=True)
    stage = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('accepted', 'Accepted'),
                              ('rejected', 'Rejected')], string='Stage', default='draft')
    patient = fields.Many2one('patients', string='Patient')
    quotation_treatment_ids = fields.One2many('quotations.treatment', 'quotation',
                                              string='Treatments')
    age = fields.Integer(string='Age', related='patient.age')
    gender = fields.Selection(string='Gender', related='patient.gender')
    medical_histiory = fields.Many2many(string='Medical history', related='patient.medical_histiory')
    quotation_date = fields.Date(string='Date', default=fields.Date.today)
    expiration_date = fields.Date(string='Expiration date',
                                  default=lambda self: fields.Date.today() + relativedelta(months=1))

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"Quota-{record.id}"
        return record
