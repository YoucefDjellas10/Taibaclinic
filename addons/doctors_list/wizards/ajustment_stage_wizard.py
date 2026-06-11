from odoo import fields, models
from odoo.exceptions import UserError


class AdjustmentStageWizard(models.TransientModel):
    _name = "adjustment.stage.wizard"
    _description = "Adjustment stage Wizard"

    order_id = fields.Many2one('dental.lab.order', string='Lab Order')
    rework_reason = fields.Text(string='Reword Reason')

    def confirme_action(self):
        self.ensure_one()
        if not self.rework_reason:
            raise UserError("Please enter th reason.")
        else:
            self.order_id.write({
                'rework_reason': self.rework_reason,
                'state': 'rework',
            })
        return {'type': 'ir.actions.act_window_close'}
