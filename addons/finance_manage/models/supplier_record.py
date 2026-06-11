from odoo import fields, models, api


class SupplierRecord(models.Model):
    _name = 'supplier.record'
    _description = 'supplier list'

    name = fields.Char(string='Name')
    purchase_ids = fields.One2many('purchase.order.record', 'supplier_id', string='Purchases')
    total_orders_amount = fields.Monetary(
        string='Total Orders Amount',
        currency_field='currency_id',
        compute='_compute_financial_summary',
        store=True,
    )

    total_paid_amount = fields.Monetary(
        string='Total Paid Amount',
        currency_field='currency_id',
        compute='_compute_financial_summary',
        store=True,
    )

    remaining_amount = fields.Monetary(
        string='Remaining Amount',
        currency_field='currency_id',
        compute='_compute_financial_summary',
        store=True,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.ref('base.DZD'),
    )

    @api.depends(
        'purchase_ids',
        'purchase_ids.total',
        'purchase_ids.paid_amount',
        'purchase_ids.payment_status',
        'purchase_ids.status',
    )
    def _compute_financial_summary(self):
        for supplier in self:
            received_orders = supplier.purchase_ids.filtered(lambda o: o.status == 'received')

            supplier.total_orders_amount = sum(received_orders.mapped('total'))
            supplier.total_paid_amount = sum(
                received_orders.filtered(lambda o: o.payment_status == 'paid').mapped('paid_amount')
            )
            supplier.remaining_amount = supplier.total_orders_amount - supplier.total_paid_amount

