from odoo import fields, models, api
from odoo.exceptions import UserError


class AppointmentCancelWizard(models.TransientModel):
    _name = 'appointment.cancel.wizard'
    _description = 'Wizard to cancel an appointment with a reason'

    appointment_id = fields.Many2one(
        'appointment.record',
        string='Appointment',
        required=True,
        readonly=True,
    )
    cancel_reason = fields.Text(
        string='Cancellation Reason',
        required=True,
    )

    def action_confirm_cancel(self):
        self.ensure_one()
        if not self.cancel_reason or not self.cancel_reason.strip():
            raise UserError('Please provide a cancellation reason.')
        self.appointment_id.write({
            'status': 'cancelled',
            'cancel_reason': self.cancel_reason,
        })
        return {'type': 'ir.actions.act_window_close'}