from odoo import fields, models, api
from odoo.exceptions import UserError


class AppointmentCancelWizard(models.TransientModel):
    _name = 'contact.stage.wizard'
    _description = 'Wizard to make stage on contacted'

    patient_id = fields.Many2one(
        'patients',
        string='Patient',
        required=True,
        readonly=True,
    )
    type = fields.Selection([
        ('call', 'Call'),
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('whatsapp_call', 'Whatsapp call'),
        ('whatsapp_message', 'Whatsapp message'),
        ('facebook_call', 'Facebook Call'),
        ('facebook_message', 'Facebook Message'),
        ('instagram_call', 'Instagram Call'),
        ('instagram_message', 'Instagram Message'),
        ('tiktok_call', 'TikTok Call'),
        ('tiktok_message', 'TikTok Message'),
    ], string='Contact type', required=True, tracking=True)
    report = fields.Text(string='Report')

    def action_confirm_cancel(self):
        self.ensure_one()
        if not self.type or not self.type.strip():
            raise UserError('Please provide a contact type.')
        self.patient_id.write({
            'stage': 'contacted',
        })
        self.env['contact.record'].create({
            'patient': self.patient_id.id,
            'type': self.type,
            'report': self.report,
        })
        return {'type': 'ir.actions.act_window_close'}
