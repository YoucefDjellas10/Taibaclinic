from odoo import models, fields


class AppProductLine(models.Model):
    _name = 'app.products'
    _description = 'Appointments products lines'

    appointment_id = fields.Many2one(
        'appointment.record',
        string='Appointment',
        required=True,
        ondelete='cascade'
    )

    product = fields.Many2one('product.record', string='Product', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)


class AppointmentInherit(models.Model):
    _inherit = 'appointment.record'

    product_ids = fields.One2many('app.products', 'appointment_id', string='Lines')
    status = fields.Selection()

    def action_complete(self):
        for line in self.product_ids:
            line.product.remaining_qt -= line.quantity
            line.product.appointment_ids = [(4, self.id)]
        self.write({'status': 'completed'})
