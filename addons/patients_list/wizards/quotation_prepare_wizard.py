from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class QuotationsPrepareWizard(models.Model):
    _name = 'quotations.prepare.wizard'
    _description = 'wizard quotations for patients'

    patient_id = fields.Many2one(
        'patients',
        string='Patient',
        required=True,
        readonly=True,
    )
    stage = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('accepted', 'Accepted'),
                              ('rejected', 'Rejected')], string='Stage', default='confirmed')
    patient = fields.Many2one('patients', string='Patient')
    description = fields.Text(string='Description')
    age = fields.Integer(string='Age', related='patient_id.age')
    gender = fields.Selection(string='Gender', related='patient_id.gender')
    medical_histiory = fields.Many2many(string='Medical history', related='patient_id.medical_histiory')
    quotation_date = fields.Date(string='Date', default=fields.Date.today)
    expiration_date = fields.Date(string='Expiration date',
                                  default=lambda self: fields.Date.today() + relativedelta(months=1))
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    gross_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Gross Total')
    discount = fields.Monetary(currency_field='currency', string='Discount')
    net_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Net Total')
    quotation_treatment_ids = fields.One2many('quotations.treatment.wizard', 'quotation',
                                              string='Treatments')

    @api.depends('quotation_treatment_ids.total', 'discount')
    def _compute_totals(self):
        for record in self:
            gross = sum(record.quotation_treatment_ids.mapped('total'))
            record.gross_total = gross
            record.net_total = gross - (record.discount or 0.0)

    def confirm_action(self):
        self.ensure_one()
        if not self.quotation_treatment_ids or not self.patient_id or not self.quotation_date or not self.expiration_date:
            raise UserError('Please provide a value for all fields.')
        if self.net_total <= 0:
            raise UserError('the quotation cannot be free.')

        self.patient_id.write({
            'stage': 'negotiation',
        })

        quotation = self.env['quotations'].create({
            'stage': self.stage,
            'doctor': self.doctor.id,
            'patient': self.patient_id.id,
            'description': self.description,
            'quotation_date': self.quotation_date,
            'expiration_date': self.expiration_date,
            'currency': self.currency.id,
            'discount': self.discount,
        })

        for line in self.quotation_treatment_ids:
            self.env['quotations.treatment'].create({
                'quotation': quotation.id,
                'treatment': line.treatment.id,
                'quantity': line.quantity,
                'currency': line.currency.id,
                'price': line.price,
                'teeth': [(6, 0, line.teeth.ids)],
            })

        return {'type': 'ir.actions.act_window_close'}


class QuotationsTreatmentWizard(models.Model):
    _name = 'quotations.treatment.wizard'
    _description = 'wizard quotations Treatment for patients'

    quotation = fields.Many2one('quotations.prepare.wizard', string='Quotation')
    treatment = fields.Many2one('treatments', string='Treatment')
    quantity = fields.Integer(string='Qte', default="1")
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    price = fields.Monetary(string='Price', currency_field='currency', related='treatment.price')
    total = fields.Monetary(string='Total', currency_field='currency', compute='computed_total')
    teeth = fields.Many2many('teeth', string='Teeth')

    @api.depends('price', 'quantity')
    def computed_total(self):
        for record in self:
            record.total = record.price * record.quantity


