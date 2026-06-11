from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseReceiveWizard(models.TransientModel):
    _name = "purchase.receive.wizard"
    _description = "Purchase Receive & Payment Wizard"

    order_id = fields.Many2one('purchase.order.record', required=True)
    is_payment_only = fields.Boolean(default=False)  # True = already received, just paying

    is_paid = fields.Boolean(string='Paid ?', default=False)
    amount = fields.Monetary(string='Amount Paid', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.ref('base.DZD'))

    def _create_expense(self, amount):
        expense_type = self.env['expense.type.record'].search(
            [('name', '=', 'Purchase')], limit=1
        )
        if expense_type:
            self.env['expense.record'].create({
                'type': expense_type.id if expense_type else False,
                'amount': amount,
                'currency': self.currency_id.id,
                'purchase': self.order_id.id,
                'note': f"Auto-generated from {self.order_id.name}",
            })

    def action_confirm(self):
        self.ensure_one()
        if self.is_paid and self.amount <= 0:
            raise UserError("Please enter a valid paid amount.")

        if self.is_payment_only:
            self.order_id.write({
                'payment_status': 'paid',
                'paid_amount': self.amount,
                'payment_date': fields.Date.today(),
                'paid_by': self.env.uid,
            })
            if self.is_paid:
                self._create_expense(self.amount)
        else:
            self.order_id.action_confirm_receive(
                is_paid=self.is_paid,
                paid_amount=self.amount
            )
            if self.is_paid:
                self._create_expense(self.amount)
        return {'type': 'ir.actions.act_window_close'}