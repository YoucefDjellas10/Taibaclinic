from odoo import fields, models
from odoo.exceptions import UserError


class SendOrderWizard(models.TransientModel):
    _name = "send.order.wizard"
    _description = "Send Lab Order Wizard"

    order_id = fields.Many2one('dental.lab.order', string='Lab Order')
    expected_date = fields.Date(string='Expected Reception Date')

    def confirme_action(self):
        self.ensure_one()
        if not self.expected_date:
            raise UserError("Please enter a valid date.")
        else:
            self.order_id.write({
                'expected_date': self.expected_date,
                'state': 'sent',
                'sent_date': fields.Date.today()
            })
        return {'type': 'ir.actions.act_window_close'}
