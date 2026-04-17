from odoo import fields, models, api


class AppointmentRecord(models.Model):
    _name = 'appointment.record'
    _description = 'Appointment for patients'

    name = fields.Char(string='ID', readonly=True)
    patient = fields.Many2one('patients', string='Patient', required=True)
    date = fields.Datetime(string='Date', required=True)
    reason = fields.Selection([
        ('consultation', 'General Consultation'),
        ('checkup', 'Dental Check-up'),
        ('cleaning', 'Scaling / Cleaning'),
        ('whitening', 'Teeth Whitening'),
        ('cavity', 'Cavity Treatment'),
        ('extraction', 'Tooth Extraction'),
        ('implant', 'Dental Implant'),
        ('prosthesis', 'Dental Prosthesis'),
        ('crown', 'Dental Crown'),
        ('veneer', 'Veneers'),
        ('orthodontics', 'Orthodontics'),
        ('root_canal', 'Root Canal'),
        ('emergency', 'Emergency'),
        ('oral_surgery', 'Oral Surgery'),
        ('tooth_pain', 'Tooth Pain'),
        ('pediatric', 'Pediatric Dentistry'),
        ('xray', 'X-Ray / Scan'),
        ('treatment_plan', 'Treatment Plan / Quote'),
        ('followup', 'Follow-up'),
        ('other', 'Other'),
    ], string='Appointment Reason', required=True)
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Treatment'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='scheduled', tracking=True)
    note = fields.Text(string='Note')

    description = fields.Text(string='Description')
    age = fields.Integer(string='Age', related='patient.age')
    gender = fields.Selection(string='Gender', related='patient.gender')
    medical_histiory = fields.Many2many(string='Medical history', related='patient.medical_histiory')
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    gross_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Gross Total')
    discount = fields.Monetary(currency_field='currency', string='Discount')
    net_total = fields.Monetary(currency_field='currency', compute='_compute_totals', string='Net Total')
    lines_ids = fields.One2many('treatment.plan.lines', 'appointment', string='Lines')
    patient_type = fields.Selection(string='Patient Type', related="patient.patient_type")
    doctor = fields.Many2one('doctors', string="Doctor")
    payment_ids = fields.One2many('patient.payment', 'appointment', string='Payments')
    deal_ids = fields.One2many('treatment.plan', 'appointment', string="Deals")

    def action_add_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Payment',
            'res_model': 'patient.payment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_appointment': self.id,
                'default_patient': self.patient.id,
            }
        }

    def action_add_deals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Deal',
            'res_model': 'treatment.plan',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_appointment': self.id,
                'default_patient': self.patient.id,
            }
        }

    @api.depends('lines_ids.total', 'discount')
    def _compute_totals(self):
        for record in self:
            gross = sum(record.lines_ids.mapped('total'))
            record.gross_total = gross
            record.net_total = gross - (record.discount or 0.0)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"App-{record.id}"
        return record


