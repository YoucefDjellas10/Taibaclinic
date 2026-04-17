from odoo import models, fields, api
from datetime import date


class Prescription(models.Model):
    _name = 'patient.prescription'
    _description = 'Patient Prescription'
    _rec_name = 'name'

    name = fields.Char(string="Reference", default="New", copy=False)
    patient_id = fields.Many2one('patients', string="Patient", required=True)
    doctor_name = fields.Char(string="Doctor", required=True)
    date = fields.Date(string="Date", default=fields.Date.today)

    line_ids = fields.One2many('prescription.line', 'prescription_id', string="Medications")

    note = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('patient.prescription') or 'New'
        return super().create(vals_list)