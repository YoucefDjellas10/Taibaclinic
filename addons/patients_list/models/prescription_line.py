from odoo import models, fields


class PrescriptionLine(models.Model):
    _name = 'prescription.line'
    _description = 'Prescription Line'

    prescription_id = fields.Many2one('patient.prescription', string="Prescription")
    medication_id = fields.Many2one('medical.medicine', string="Medicine", required=True)

    dosage = fields.Char(string="Dosage")
    frequency = fields.Char(string="Frequency")
    duration = fields.Char(string="Duration")

    instructions = fields.Char(string="Instructions")