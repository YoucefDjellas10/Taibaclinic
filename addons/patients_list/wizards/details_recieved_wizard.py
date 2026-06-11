from odoo import fields, models, api
from odoo.exceptions import UserError


class DetailsReceivedWizard(models.TransientModel):
    _name = 'details.received.wizard'
    _description = 'Wizard to make stage quotation preparation'

    patient_id = fields.Many2one(
        'patients',
        string='Patient',
        required=True,
        readonly=True,
    )

    name = fields.Char(string='Name')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    def action_confirm_action(self):
        self.ensure_one()
        if not self.name or not self.attachment_ids:
            raise UserError('Please provide a value for all fields.')

        self.env['patient.attachments'].create({
            'patient': self.patient_id.id,
            'name': self.name,
            'attachment_ids': self.attachment_ids,
        })
        self.patient_id.write({
            'stage': 'quotation_preparation',
        })
        return {'type': 'ir.actions.act_window_close'}
