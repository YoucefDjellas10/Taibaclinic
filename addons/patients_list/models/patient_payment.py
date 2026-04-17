from odoo import fields, models, api


class AppointmentRecord(models.Model):
    _name = 'patient.payment'
    _description = 'Payments for patients'

    name = fields.Char(string='ID', readonly=True)
    patient = fields.Many2one('patients', string='Patient')
    appointment = fields.Many2one('appointment.record', string='Appointment')
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    amount = fields.Monetary(currency_field='currency',  string='Amount')
    note = fields.Text(string='Note')
    doctor = fields.Many2one('doctors', string="Doctor")

    @api.onchange('appointment')
    def _onchange_appointment_set_doctor(self):
        for record in self:
            if record.appointment and record.appointment.doctor:
                record.doctor = record.appointment.doctor

    @api.model
    def create(self, vals_list):
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        for vals in vals_list:
            # Si appointment existe et patient n'existe pas
            if vals.get('appointment') and not vals.get('patient'):
                appointment = self.env['appointment.record'].browse(vals['appointment'])
                if appointment.patient:
                    vals['patient'] = appointment.patient.id

            if vals.get('appointment') and not vals.get('doctor'):
                appointment = self.env['appointment.record'].browse(vals['appointment'])
                if appointment.doctor:
                    vals['doctor'] = appointment.doctor.id

        records = super().create(vals_list)
        for record in records:
            record.name = f"Pay-{record.id}"
        return records
