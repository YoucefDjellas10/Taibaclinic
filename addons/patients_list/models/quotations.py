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
    description = fields.Text(string='Description')
    age = fields.Integer(string='Age', related='patient.age')
    gender = fields.Selection(string='Gender', related='patient.gender')
    medical_histiory = fields.Many2many(string='Medical history', related='patient.medical_histiory')
    quotation_date = fields.Date(string='Date', default=fields.Date.today)
    expiration_date = fields.Date(string='Expiration date',
                                  default=lambda self: fields.Date.today() + relativedelta(months=1))
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    gross_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Gross Total')
    discount = fields.Monetary(currency_field='currency', string='Discount')
    net_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Net Total')

    @api.depends('quotation_treatment_ids.total', 'discount')
    def _compute_totals(self):
        for record in self:
            gross = sum(record.quotation_treatment_ids.mapped('total'))
            record.gross_total = gross
            record.net_total = gross - (record.discount or 0.0)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"Quota-{record.id}"
        return record
