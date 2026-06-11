from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DeclarePaymentWizard(models.TransientModel):
    _name = 'declare.payment.wizard'
    _description = 'Declare Payment Wizard'

    order_id = fields.Many2one(
        'dental.lab.order',
        string='Order',
    )
    amount_total = fields.Monetary(
        string='Order Total',
        readonly=True,
        currency_field='currency_id',
    )
    amount_already_paid = fields.Monetary(
        string='Already Paid',
        readonly=True,
        currency_field='currency_id',
    )
    amount_remaining = fields.Monetary(
        string='Remaining',
        readonly=True,
        currency_field='currency_id',
    )
    amount_to_pay = fields.Monetary(
        string='Amount to Pay',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='order_id.currency_id',
        readonly=True,
    )

    @api.constrains('amount_to_pay')
    def _check_amount(self):
        for wizard in self:
            if wizard.amount_to_pay <= 0:
                raise ValidationError("Amount to pay must be greater than zero.")
            if wizard.amount_to_pay > wizard.amount_remaining:
                raise ValidationError(
                    f"Amount to pay ({wizard.amount_to_pay}) cannot exceed "
                    f"the remaining amount ({wizard.amount_remaining})."
                )

    def action_confirm_payment(self):
        self.ensure_one()
        order = self.order_id
        new_paid = order.amount_paid + self.amount_to_pay

        # Update invoice_status
        if new_paid >= order.amount_total:
            new_status = 'paid'
        elif new_paid > 0:
            new_status = 'partial'
        else:
            new_status = 'to_pay'

        order.write({
            'amount_paid': new_paid,
            'invoice_status': new_status,
        })

        # Create expense record
        self.env['expense.record'].create({
            'type': 1,
            'amount': self.amount_to_pay,
            'Date': fields.Datetime.now(),
            'currency': order.currency_id.id,
        })