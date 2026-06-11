from odoo import fields, models, api
from odoo.exceptions import UserError


class LostStageWizard(models.TransientModel):
    _name = 'lost.stage.wizard'
    _description = 'Wizard to make stage lost'

    patient_id = fields.Many2one(
        'patients',
        string='Patient',
        required=True,
        readonly=True,
    )
    lost_reason_id = fields.Many2one('lost.reason.record', string='Reason')

    def action_confirm_action(self):
        self.ensure_one()
        if not self.lost_reason_id:
            raise UserError('Please provide a reason.')
        self.patient_id.write({
            'stage': 'lost',
            'lost_reason_id': self.lost_reason_id
        })
        return {'type': 'ir.actions.act_window_close'}
