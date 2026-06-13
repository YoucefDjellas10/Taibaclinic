from odoo import fields, models
from odoo.exceptions import UserError


class CreateLabOrderWizard(models.TransientModel):
    _name = 'create.lab.order.wizard'
    _description = 'Create Lab Order from Appointment'

    appointment_id = fields.Many2one('appointment.record', string='Appointment', required=True)

    # doctor pas required, calculé depuis appointment
    doctor_id = fields.Many2one('doctors', string='Doctor')

    lab_id = fields.Many2one('laboratory.list', string='Laboratory', required=True)
    work_type = fields.Selection([
        ('fixed', 'Fixed Prosthesis'),
        ('removable', 'Removable Prosthesis'),
        ('ortho', 'Orthodontics'),
        ('implant', 'Implantology'),
        ('guard', 'Night Guard / Splint'),
        ('provisional', 'Provisional'),
        ('other', 'Other'),
    ], string='Work Type', required=True, default='fixed')

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Urgent'),
        ('2', 'Very Urgent'),
    ], string='Priority', default='0')

    impression_type = fields.Selection([
        ('physical', 'Physical Impression'),
        ('digital', 'Digital Impression (STL)'),
        ('both', 'Both'),
    ], string='Impression Type', default='physical')

    general_shade = fields.Selection([
        ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A3.5', 'A3.5'), ('A4', 'A4'),
        ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'),
        ('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'),
        ('D2', 'D2'), ('D3', 'D3'), ('D4', 'D4'),
    ], string='General Shade (Vita)')

    tracking_number = fields.Char(string='Tracking / Delivery Note No.')
    notes = fields.Text(string='Notes for the Technician')

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'DZD')], limit=1),
    )

    line_ids = fields.One2many('create.lab.order.wizard.line', 'wizard_id', string='Order Lines')

    def action_create_lab_order(self):
        self.ensure_one()

        # Calculer doctor_id depuis appointment
        doctor_id = self.doctor_id.id
        if not doctor_id and self.appointment_id and self.appointment_id.doctor:
            doctor_id = self.appointment_id.doctor.id

        if not doctor_id:
            raise UserError("No doctor found. Please set a doctor or link a valid appointment.")

        order = self.env['dental.lab.order'].create({
            'appointment': self.appointment_id.id,
            'doctor_id': doctor_id,
            'lab_id': self.lab_id.id,
            'work_type': self.work_type,
            'priority': self.priority,
            'impression_type': self.impression_type,
            'general_shade': self.general_shade,
            'tracking_number': self.tracking_number,
            'notes': self.notes,
            'line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'prosthesis_type': line.prosthesis_type,
                'material': line.material,
                'tooth_numbers': [(6, 0, line.tooth_numbers.ids)],
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }) for line in self.line_ids],
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Lab Order',
            'res_model': 'dental.lab.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }


class CreateLabOrderWizardLine(models.TransientModel):
    _name = 'create.lab.order.wizard.line'
    _description = 'Wizard Lab Order Line'

    wizard_id = fields.Many2one('create.lab.order.wizard', ondelete='cascade')
    product_id = fields.Many2one('laboratory.product', string='Product', required=True)
    prosthesis_type = fields.Selection([
        ('crown_pfm', 'Porcelain-Fused-to-Metal Crown'),
        ('crown_zirconia', 'Zirconia Crown'),
        ('crown_emax', 'e.max Crown'),
        ('inlay', 'Inlay'),
        ('onlay', 'Onlay'),
        ('bridge', 'Bridge'),
        ('veneer', 'Veneer'),
        ('removable_partial', 'Partial Denture (Stellite)'),
        ('removable_complete', 'Complete Denture'),
        ('implant_abutment', 'Implant Abutment'),
        ('other', 'Other'),
    ], string='Prosthesis Type', required=True)
    material = fields.Selection([
        ('zirconia', 'Zirconia'),
        ('emax', 'Lithium Disilicate (e.max)'),
        ('metal_ceramic', 'Porcelain-Fused-to-Metal'),
        ('full_metal', 'Metal'),
        ('resin', 'Resin'),
        ('pmma', 'PMMA'),
        ('other', 'Other'),
    ], string='Material')
    tooth_numbers = fields.Many2many('teeth', string='Tooth Numbers (FDI)')
    quantity = fields.Integer(string='Quantity', default=1, required=True)
    price_unit = fields.Float(string='Unit Price', default=0.0)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env['res.currency'].search([('name', '=', 'DZD')], limit=1),
    )
    price_total = fields.Monetary(
        compute=lambda self: [setattr(l, 'price_total', l.quantity * l.price_unit) for l in self],
        currency_field='currency_id',
    )