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

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"App-{record.id}"
        return record


