from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrderRecord(models.Model):
    _name = "purchase.order.record"
    _description = "Purchase Order"

    name = fields.Char(string='Reference', readonly=True)

    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')

    # ── Payment fields ─────────────────────────────────────────────
    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ], string='Payment Status', default='unpaid', readonly=True)

    paid_amount = fields.Monetary(
        string='Paid Amount',
        currency_field='currency',
        readonly=True
    )
    payment_date = fields.Date(string='Payment Date', readonly=True)
    paid_by = fields.Many2one('res.users', string='Paid By', readonly=True)

    # ── Main fields ────────────────────────────────────────────────
    supplier_id = fields.Many2one('supplier.record', string='Supplier', required=True)
    order_date = fields.Datetime(string='Order Date', default=fields.Datetime.now)
    expected_date = fields.Date(string='Expected Delivery Date')

    currency = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.ref('base.DZD')
    )

    line_ids = fields.One2many(
        'purchase.order.line',
        'order_id',
        string='Order Lines'
    )

    total = fields.Monetary(
        string='Total',
        currency_field='currency',
        compute='_compute_total',
        store=True
    )

    note = fields.Text(string='Note')

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'purchase_order_attachment_rel',
        'order_id',
        'attachment_id',
        string='Attachments'
    )

    # ── Audit fields ───────────────────────────────────────────────
    confirmed_by = fields.Many2one('res.users', string='Confirmed by', readonly=True)
    confirmation_date = fields.Date(string='Confirmation date', readonly=True)
    received_by = fields.Many2one('res.users', string='Received by', readonly=True)
    reception_date = fields.Date(string='Reception date', readonly=True)
    cancelled_by = fields.Many2one('res.users', string='Cancelled by', readonly=True)
    cancellation_date = fields.Date(string='Cancellation date', readonly=True)

    # ── Compute ────────────────────────────────────────────────────
    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(rec.line_ids.mapped('subtotal'))

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"PO-{record.id}"
        return record

    # ── Status actions ─────────────────────────────────────────────
    def confirme_action(self):
        for record in self:
            if record.status != 'draft':
                raise UserError(f"Only draft orders can be confirmed ('{record.name}' is {record.status}).")
            record.write({
                'status': 'confirmed',
                'confirmed_by': self.env.uid,
                'confirmation_date': fields.Date.today(),
            })

    def receive_action(self):
        """Opens the payment wizard popup."""
        self.ensure_one()
        if self.status != 'confirmed':
            raise UserError("Only confirmed orders can be received.")
        wizard = self.env['purchase.receive.wizard'].create({
            'order_id': self.id,
            'amount': self.total,
            'currency_id': self.currency.id,
            'is_payment_only': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receive Order',
            'res_model': 'purchase.receive.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_confirm_receive(self, is_paid=False, paid_amount=0):
        """Called by the wizard after user confirms reception."""
        for record in self:
            # Increment stock for each line
            for line in record.line_ids:
                product = line.product
                product.remaining_qt += line.quantity
                product.purchase_ids = [(4, record.id)]

            vals = {
                'status': 'received',
                'received_by': self.env.uid,
                'reception_date': fields.Date.today(),
            }

            if is_paid:
                vals.update({
                    'payment_status': 'paid',
                    'paid_amount': paid_amount,
                    'payment_date': fields.Date.today(),
                    'paid_by': self.env.uid,
                })
            else:
                vals['payment_status'] = 'unpaid'

            record.write(vals)

    def action_mark_as_paid(self):
        """Opens wizard just for payment (order already received)."""
        self.ensure_one()
        if self.status != 'received':
            raise UserError("Only received orders can be marked as paid.")
        if self.payment_status == 'paid':
            raise UserError(f"'{self.name}' is already paid.")
        wizard = self.env['purchase.receive.wizard'].create({
            'order_id': self.id,
            'amount': self.total,
            'currency_id': self.currency.id,
            'is_payment_only': True,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mark as Paid',
            'res_model': 'purchase.receive.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def cancel_action(self):
        for record in self:
            if record.status in ('received', 'cancelled'):
                raise UserError(f"'{record.name}' cannot be cancelled (status: {record.status}).")
            record.write({
                'status': 'cancelled',
                'cancelled_by': self.env.uid,
                'cancellation_date': fields.Date.today(),
            })


class PurchaseOrderLine(models.Model):
    _name = "purchase.order.line"
    _description = "Purchase Order Line"

    order_id = fields.Many2one(
        'purchase.order.record',
        string='Purchase Order',
        required=True,
        ondelete='cascade'
    )

    product = fields.Many2one('product.record', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Monetary(string='Unit Price', currency_field='currency_id')

    currency_id = fields.Many2one(
        related='order_id.currency',
        store=True
    )

    subtotal = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_subtotal',
        store=True
    )

    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
