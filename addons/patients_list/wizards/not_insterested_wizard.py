from odoo import fields, models, api
from odoo.exceptions import UserError


class NotInterestedWizard(models.TransientModel):
    _name = 'not.interested.wizard'
    _description = 'Wizard to make stage not interested'

    patient_id = fields.Many2one(
        'patients',
        string='Patient',
        required=True,
        readonly=True,
    )
    not_interested_reason = fields.Many2one('not.interested.reason', string='Reason')

    def action_confirm_action(self):
        self.ensure_one()
        if not self.not_interested_reason :
            raise UserError('Please provide a reason.')
        self.patient_id.write({
            'stage': 'not_interested',
            'not_interested_reason': self.not_interested_reason
        })
        return {'type': 'ir.actions.act_window_close'}
