from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class DentalLabOrder(models.Model):
    _name = 'dental.lab.order'
    _description = 'Dental Lab Order'

    name = fields.Char(
        string='Reference',
        copy=False,
        readonly=True,
        tracking=True,
    )

    work_type = fields.Selection([
        ('fixed', 'Fixed Prosthesis'),
        ('removable', 'Removable Prosthesis'),
        ('ortho', 'Orthodontics'),
        ('implant', 'Implantology'),
        ('guard', 'Night Guard / Splint'),
        ('provisional', 'Provisional'),
        ('other', 'Other'),
    ], string='Work Type', required=True, default='fixed', tracking=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Urgent'),
        ('2', 'Very Urgent'),
    ], string='Priority', default='0', tracking=True)

    lab_id = fields.Many2one(
        'laboratory.list',
        string='Laboratory',
        required=True,
    )
    doctor_id = fields.Many2one(
        'doctors',
        string='Doctor',
        required=True,
    )

    appointment = fields.Many2one('appointment.record', string='Appointment')

    # patient_id = fields.Many2one(
    #     'dental.patient',
    #     string='Patient',
    #     required=True,
    #     tracking=True,
    # )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env['res.currency'].search(
            [('name', '=', 'DZD')], limit=1
        ),
    )

    order_date = fields.Date(
        string='Order Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    sent_date = fields.Date(string='Sent to Lab Date')
    expected_date = fields.Date(string='Expected Reception Date')
    received_date = fields.Date(string='Actual Reception Date')
    fitting_date = fields.Date(string='Fitting Date')
    placement_date = fields.Date(string='Placement Date')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sent', 'Sent to Lab'),
        ('manufacturing', 'In Manufacturing'),
        ('fitting', 'Fitting Session'),
        ('rework', 'Returned for Adjustment'),
        ('validated', 'Validated'),
        ('delivered', 'Delivered'),
        ('placed', 'Placed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    fitting_count = fields.Integer(
        string='Fitting Sessions',
        default=0,
        help="Number of fitting sessions performed",
    )
    rework_reason = fields.Text(string='Rework Reason')

    general_shade = fields.Selection([
        ('A1', 'A1'), ('A2', 'A2'), ('A3', 'A3'), ('A3.5', 'A3.5'), ('A4', 'A4'),
        ('B1', 'B1'), ('B2', 'B2'), ('B3', 'B3'), ('B4', 'B4'),
        ('C1', 'C1'), ('C2', 'C2'), ('C3', 'C3'), ('C4', 'C4'),
        ('D2', 'D2'), ('D3', 'D3'), ('D4', 'D4'),
    ], string='General Shade (Vita)')

    impression_type = fields.Selection([
        ('physical', 'Physical Impression'),
        ('digital', 'Digital Impression (STL)'),
        ('both', 'Both'),
    ], string='Impression Type', default='physical')

    tracking_number = fields.Char(string='Tracking / Delivery Note No.')

    line_ids = fields.One2many(
        'dental.lab.order.line',
        'order_id',
        string='Order Lines',
        copy=True,
    )

    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amount_total',
        store=True,
        currency_field='currency_id',
        tracking=True,
    )

    invoice_status = fields.Selection([
        ('not_billed', 'Not Billed'),
        ('to_pay', 'To Pay'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ], string='Lab Payment Status', default='to_pay', tracking=True)

    notes = fields.Text(string='Notes for the Technician')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'dental_lab_order_attachment_rel',
        'order_id', 'attachment_id',
        string='Attachments (photos, X-rays, STL)',
    )
    amount_paid = fields.Monetary(
        string='Amount Paid',
        default=0.0,
        currency_field='currency_id',
        tracking=True,
    )

    amount_remaining = fields.Monetary(
        string='Remaining Amount',
        compute='_compute_amount_remaining',
        store=True,
        currency_field='currency_id',
        tracking=True,
    )

    @api.depends('amount_total', 'amount_paid')
    def _compute_amount_remaining(self):
        for order in self:
            order.amount_remaining = order.amount_total - order.amount_paid

    def action_declare_payment(self):
        self.ensure_one()
        wizard = self.env['declare.payment.wizard'].create({
            'order_id': self.id,
            'amount_total': self.amount_total,
            'amount_already_paid': self.amount_paid,
            'amount_remaining': self.amount_remaining,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Declare Payment',
            'res_model': 'declare.payment.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.depends('line_ids.price_total')
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = sum(order.line_ids.mapped('price_total'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dental.lab.order') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        for order in self:
            if not order.line_ids:
                raise UserError("Cannot confirm an empty order.")
            order.state = 'confirmed'

    def action_send_to_lab(self):
        self.ensure_one()
        wizard = self.env['send.order.wizard'].create({
            'order_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send Order',
            'res_model': 'send.order.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_start_manufacturing(self):
        self.state = 'manufacturing'

    def action_fitting(self):
        for order in self:
            order.state = 'fitting'
            order.fitting_count += 1
            order.fitting_date = fields.Date.today()

    def action_rework(self):
        self.ensure_one()
        wizard = self.env['adjustment.stage.wizard'].create({
            'order_id': self.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reword action',
            'res_model': 'adjustment.stage.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_validate(self):
        self.state = 'validated'

    def action_deliver(self):
        self.write({'state': 'delivered', 'received_date': fields.Date.today()})

    def action_place(self):
        self.write({'state': 'placed', 'placement_date': fields.Date.today()})

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reset_to_draft(self):
        self.state = 'draft'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('appointment') and not vals.get('doctor_id'):
                appointment = self.env['appointment.record'].browse(vals['appointment'])
                if appointment.doctor:
                    vals['doctor_id'] = appointment.doctor.id
        records = super().create(vals_list)
        for record in records:
            record.name = f"Lab-order-{record.id}"

        return records

    def action_print_report(self):
        self.ensure_one()
        return self.env.ref('doctors_list.action_report_dental_lab_order').report_action(self)


class DentalLabOrderLine(models.Model):
    _name = 'dental.lab.order.line'
    _description = 'Dental Lab Order Line'
    _rec_name = 'product_id'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    order_id = fields.Many2one(
        'dental.lab.order',
        string='Order',
        required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'laboratory.product',
        string='Product',
        required=True,
    )

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
    price_unit = fields.Float(string='Unit Price', required=True, default=0.0)

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env['res.currency'].search(
            [('name', '=', 'DZD')], limit=1
        ),
    )

    price_total = fields.Monetary(
        string='Total',
        compute='_compute_price_total',
        store=True,
        currency_field='currency_id',
    )

    @api.depends('quantity', 'price_unit')
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.price_unit

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError("Quantity must be greater than zero.")


class AppointmentInherit(models.Model):
    _inherit = 'appointment.record'

    Labo_ids = fields.One2many('dental.lab.order', 'appointment', string='Lab lines')
    currency = fields.Many2one('res.currency',
                               string='Currency',
                               default=lambda self: self.env.ref('base.DZD'))
    total_payments_labo = fields.Monetary(currency_field='currency', string='Total labo',
                                          compute='_compute_total_payments_labo', store=True)
    doctor = fields.Many2one('doctors', string="Doctor")

    @api.depends('Labo_ids.amount_total')
    def _compute_total_payments_labo(self):
        for record in self:
            total = sum(record.Labo_ids.mapped('amount_total'))
            record.total_payments_labo = total

    def action_open_create_lab_order_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Lab Order',
            'res_model': 'create.lab.order.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_appointment_id': self.id,
                'default_doctor_id': self.doctor.id if self.doctor else False,
            },
        }
