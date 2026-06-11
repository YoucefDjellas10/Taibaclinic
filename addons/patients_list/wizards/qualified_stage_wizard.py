from odoo import fields, models, api
from odoo.exceptions import UserError


class QualifiedWizard(models.TransientModel):
    _name = 'qualified.wizard'
    _description = 'Wizard to make stage qualified'

    patient_id = fields.Many2one(
        'patients',
        string='Patient',
        required=True,
        readonly=True,
    )
    interested_id = fields.Many2one('interest.record', string='Interest')
    medical_histiory = fields.Many2many('medical.history', string='Medical history')
    gender = fields.Selection([('Mr', 'Mr'), ('Ms', 'Ms')], string='Gender')
    birthday = fields.Date(string='Birthday')

    def action_confirm_action(self):
        self.ensure_one()
        if not self.interested_id or not self.medical_histiory or not self.gender or not self.birthday:
            raise UserError('Please provide a value for all fields.')
        self.patient_id.write({
            'stage': 'qualified',
            'interested_id': self.interested_id,
            'medical_histiory': self.medical_histiory,
            'gender': self.gender,
            'birthday': self.birthday,
        })
        return {'type': 'ir.actions.act_window_close'}
