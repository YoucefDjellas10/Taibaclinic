from odoo import fields, models, api
from datetime import date
from odoo.exceptions import ValidationError


class Doctors(models.Model):
    _name = 'doctors'
    _description = 'Doctors list'

    name = fields.Char(string='Full name', compute='_compute_full_name', store=True)
    category = fields.Many2one('price.category', string='Category', required=True)
    account = fields.Many2one('res.users', string='Account', required=True)
    speciality = fields.Many2one('doctor.speciality', string='Speciality')
    gender = fields.Selection([('Mr', 'Mr'), ('Ms', 'Ms')], string='Gender', required=True)
    first_name = fields.Char(string='First name', required=True)
    last_name = fields.Char(string='Last name', required=True)
    birthday = fields.Date(string='Birthday', required=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    mobile = fields.Char(string='Mobile', required=True)
    nd_mobile = fields.Char(string='2nd Mobile')
    treatments_lines = fields.One2many('treatment.plan.lines', 'doctor', string='Treatments')
    percentage = fields.Integer(string='Percentage %')

    @api.depends('birthday')
    def _compute_age(self):
        today = date.today()
        for rec in self:
            if rec.birthday:
                rec.age = today.year - rec.birthday.year - (
                        (today.month, today.day) < (rec.birthday.month, rec.birthday.day)
                )
            else:
                rec.age = 0

    @api.depends('gender', 'first_name', 'last_name')
    def _compute_full_name(self):
        for rec in self:
            parts = []
            if rec.gender:
                parts.append(rec.gender)
            if rec.first_name:
                parts.append(rec.first_name)
            if rec.last_name:
                parts.append(rec.last_name)

            rec.name = " ".join(parts)


class AppointmentsInherit(models.Model):
    _inherit = 'appointment.record'

    doctor = fields.Many2one('doctors', string="Doctor")
    category = fields.Many2one(string='category', related='doctor.category')


class PatientPaymentInherit(models.Model):
    _inherit = 'patient.payment'
    doctor = fields.Many2one('doctors', string="Doctor")
    category = fields.Many2one(string='category', related='doctor.category')
    appointment = fields.Many2one()

    @api.onchange('appointment')
    def _onchange_appointment_set_doctor(self):
        for record in self:
            if record.appointment and record.appointment.doctor:
                record.doctor = record.appointment.doctor


class QuotationInherit(models.Model):
    _inherit = 'quotations'

    doctor = fields.Many2one('doctors', string="Doctor")
    category = fields.Many2one(string='category', related='doctor.category')


class TreatmentPlanInherit(models.Model):
    _inherit = 'treatment.plan.lines'

    appointment = fields.Many2one()
    treatment = fields.Many2one()
    doctor = fields.Many2one(string="Doctor", related='appointment.doctor', required=True)
    category = fields.Many2one(string='category', related='doctor.category', required=True)

    price = fields.Monetary(compute='price_calculate', readonly=False, store=True)

    @api.depends('category', 'treatment')
    def price_calculate(self):
        for record in self:
            prices_list = self.env['pricing.list'].search([
                ('treatment', '=', record.treatment.id),
                ('category', '=', record.category.id),
            ], limit=1)
            if prices_list:
                record.price = prices_list.default_price
            else:
                record.price = 0

    # @api.constrains('price', 'treatment', 'category')
    # def _check_min_price(self):
    #     for record in self:
    #
    #         prices_list = self.env['pricing.list'].search([
    #             ('treatment', '=', record.treatment.id),
    #             ('category', '=', record.category.id),
    #         ], limit=1)
    #
    #         if not record.doctor and not record.appointment.doctor:
    #             raise ValidationError(
    #                 f"doctor field is required"
    #             )
    #
    #         if not record.category and not record.appointment.doctor.category:
    #             raise ValidationError(
    #                 f"doctor category field is required"
    #             )
    #
    #         if prices_list and record.price < prices_list.min_price:
    #             raise ValidationError(
    #                 f"The price {record.price} is lower than the minimum allowed price"
    #                 f"({prices_list.min_price}) for the '{record.treatment.name}' process."
    #             )


class QuotationsTreatmentInherit(models.Model):
    _inherit = 'quotations.treatment'

    quotation = fields.Many2one()
    treatment = fields.Many2one()
    doctor = fields.Many2one(string="Doctor", related='quotation.doctor')
    category = fields.Many2one(string='category', related='doctor.category')

    price = fields.Monetary(compute='price_calculate', readonly=False, store=True)

    @api.depends('category', 'treatment')
    def price_calculate(self):
        for record in self:
            prices_list = self.env['pricing.list'].search([
                ('treatment', '=', record.treatment.id),
                ('category', '=', record.category.id),
            ], limit=1)
            if prices_list:
                record.price = prices_list.default_price
            else:
                record.price = 0

    # @api.constrains('price', 'treatment', 'category')
    # def _check_min_price(self):
    #     for record in self:
    #
    #         prices_list = self.env['pricing.list'].search([
    #             ('treatment', '=', record.treatment.id),
    #             ('category', '=', record.category.id),
    #         ], limit=1)
    #
    #         if not record.doctor and not record.quotation.doctor:
    #             raise ValidationError(
    #                 f"doctor field is required"
    #             )
    #
    #         if not record.category and not record.quotation.doctor.category:
    #             raise ValidationError(
    #                 f"doctor category field is required"
    #             )
    #
    #         if prices_list and record.price < prices_list.min_price:
    #             raise ValidationError(
    #                 f"The price {record.price} is lower than the minimum allowed price"
    #                 f"({prices_list.min_price}) for the '{record.treatment.name}' process."
    #             )


class QuotationsTreatmentWizardInherit(models.Model):
    _inherit = 'quotations.treatment.wizard'

    quotation = fields.Many2one()
    treatment = fields.Many2one()
    doctor = fields.Many2one(string="Doctor", related='quotation.doctor')
    category = fields.Many2one(string='category', related='doctor.category')

    price = fields.Monetary(compute='price_calculate', readonly=False, store=True)

    @api.depends('category', 'treatment')
    def price_calculate(self):
        for record in self:
            prices_list = self.env['pricing.list'].search([
                ('treatment', '=', record.treatment.id),
                ('category', '=', record.category.id),
            ], limit=1)
            if prices_list:
                record.price = prices_list.default_price
            else:
                record.price = 0

    # @api.constrains('price', 'treatment', 'category')
    # def _check_min_price(self):
    #     for record in self:
    #
    #         prices_list = self.env['pricing.list'].search([
    #             ('treatment', '=', record.treatment.id),
    #             ('category', '=', record.category.id),
    #         ], limit=1)
    #
    #         if not record.doctor and not record.quotation.doctor:
    #             raise ValidationError(
    #                 f"doctor field is required"
    #             )
    #
    #         if not record.category and not record.quotation.doctor.category:
    #             raise ValidationError(
    #                 f"doctor category field is required"
    #             )
    #
    #         if prices_list and record.price < prices_list.min_price:
    #             raise ValidationError(
    #                 f"The price {record.price} is lower than the minimum allowed price"
    #                 f"({prices_list.min_price}) for the '{record.treatment.name}' process."
    #             )


class QuotationsPrepareWizardInherit(models.Model):
    _inherit = 'quotations.prepare.wizard'

    doctor = fields.Many2one('doctors', string="Doctor", required=True)
    category = fields.Many2one(string='category', related='doctor.category')
