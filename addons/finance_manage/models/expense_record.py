from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class ExpenseRecord(models.Model):
    _name = "expense.record"
    _description = "expense record list"

    name = fields.Char(string='id', readonly=True)
    status = fields.Selection([('draft', 'Draft'),
                               ('validated', 'Validated'),
                               ('refused', 'Refused')], string='Status', default='draft')
    type = fields.Many2one('expense.type.record', string='Type')
    Date = fields.Datetime(string='Date', default=fields.Datetime.now)
    currency = fields.Many2one('res.currency',
                               string='Currency', required=True,
                               default=lambda self: self.env.ref('base.DZD'))
    amount = fields.Monetary(currency_field='currency', string='Amount')

    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("The amount must be greater than 0.")

    note = fields.Text(string='Note')
    purchase = fields.Many2one('purchase.order.record', string='Purchase order')

    validated_by = fields.Many2one('res.users', string='Validated By', readonly=True)
    validated_date = fields.Datetime(string='Validated On', readonly=True)
    refused_by = fields.Many2one('res.users', string='Refused By', readonly=True)
    refused_date = fields.Datetime(string='Refused On', readonly=True)
    refuse_reason = fields.Text(string='Refuse Reason', readonly=True)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.name = f"Exp-{record.id}"
        return record

    def action_validate(self):
        for record in self:
            if record.status != 'draft':
                raise UserError(f"Only draft expenses can be validated ('{record.name}' is {record.status}).")
            record.write({
                'status': 'validated',
                'validated_by': self.env.uid,
                'validated_date': fields.Datetime.now(),
            })

    def action_refuse(self, reason=None):
        self.ensure_one()

        if reason is not None:
            if self.status != 'draft':
                raise UserError(f"Only draft expenses can be refused ('{self.name}' is {self.status}).")
            self.write({
                'status': 'refused',
                'refused_by': self.env.uid,
                'refused_date': fields.Datetime.now(),
                'refuse_reason': reason,
            })
            return

        wizard = self.env['expense.refuse.wizard'].create({'expense_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refuse Expense',
            'res_model': 'expense.refuse.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }