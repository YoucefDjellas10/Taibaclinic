from odoo import models, fields, api
from datetime import date


class Prescription(models.Model):
    _name = 'patient.prescription'
    _description = 'Patient Prescription'
    _rec_name = 'name'

    name = fields.Char(string="Reference", default="New", copy=False)
    patient_id = fields.Many2one('patients', string="Patient", required=True)
    appointment_id = fields.Many2one('appointment.record', string="Appointment", required=True)
    doctor_name = fields.Char(string="Doctor")
    date = fields.Date(string="Date", default=fields.Date.today)
    ordre_number = fields.Char(string="N° d'ordre", copy=False, readonly=True)

    line_ids = fields.One2many('prescription.line', 'prescription_id', string="Medications")

    note = fields.Text(string="Notes")

    def action_print_prescription(self):
        self.ensure_one()
        return self.env.ref('patients_list.action_report_prescription').report_action(self)

    def action_print_prescription_letterhead(self):
        self.ensure_one()
        return self.env.ref('patients_list.action_report_prescription_letterhead').report_action(self)

    @api.onchange('appointment_id')
    def _onchange_appointment_id(self):
        if self.appointment_id:
            self.patient_id = self.appointment_id.patient

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('patient.prescription') or 'New'
            if not vals.get('ordre_number'):
                vals['ordre_number'] = self.env['ir.sequence'].next_by_code('patient.prescription.ordre')
        return super().create(vals_list)