from odoo import fields, models, api


class TreatmentPlan(models.Model):
    _name = 'treatment.plan'
    _description = 'plan of patients treatments'

    name = fields.Char(string='ID', readonly=True)
    status = fields.Selection([('pending', 'Pending'),
                               ('refused', 'Refused'),
                               ('accepted', 'Accepted')], string='Status', default='pending', required=True)
    patient = fields.Many2one('patients', string='Patient', required=True)
    appointment = fields.Many2one('appointment.record', string='Appointment')
    description = fields.Text(string='Description')
    age = fields.Integer(string='Age', related='patient.age')
    gender = fields.Selection(string='Gender', related='patient.gender')
    medical_histiory = fields.Many2many(string='Medical history', related='patient.medical_histiory')
    deal_date = fields.Datetime(string='First', default=fields.Datetime.now)
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    gross_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Gross Total')
    discount = fields.Monetary(currency_field='currency', string='Discount')
    net_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Net Total')
    lines_ids = fields.One2many('treatment.plan.lines', 'plan', string='Lines')

    @api.depends('lines_ids.total', 'discount')
    def _compute_totals(self):
        for record in self:
            gross = sum(record.lines_ids.mapped('total'))
            record.gross_total = gross
            record.net_total = gross - (record.discount or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record.name = f"Deal-{record.id}"
        return records
