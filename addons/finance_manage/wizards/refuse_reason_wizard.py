from odoo import models, fields, api


class ExpenseRefuseWizard(models.TransientModel):
    _name = "expense.refuse.wizard"
    _description = "Expense Refuse Reason Wizard"

    expense_id = fields.Many2one('expense.record', string='Expense', required=True)
    refuse_reason = fields.Text(string='Refuse Reason')

    def action_confirm_refuse(self):
        self.ensure_one()
        self.expense_id.action_refuse(reason=self.refuse_reason)
        return {'type': 'ir.actions.act_window_close'}