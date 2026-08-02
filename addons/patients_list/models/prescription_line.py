from odoo import models, fields, api


class PrescriptionLine(models.Model):
    _name = 'prescription.line'
    _description = 'Prescription Line'

    prescription_id = fields.Many2one('patient.prescription', string="Prescription")
    medication_id = fields.Many2one('medical.medicine', string="Medicine", required=True)

    # --- Dosage: quantity + unit per intake ---
    dose_qty = fields.Selection([
        ('1/4', '1/4'), ('1/2', '1/2'), ('3/4', '3/4'),
        ('1', '1'), ('1.5', '1.5'), ('2', '2'), ('2.5', '2.5'),
        ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'),
        ('8', '8'), ('10', '10'), ('15', '15'), ('20', '20'),
        ('25', '25'), ('30', '30'), ('40', '40'), ('50', '50'),
        ('100', '100'), ('125', '125'), ('200', '200'), ('250', '250'),
        ('400', '400'), ('500', '500'), ('1000', '1000'),
    ], string="Dose")
    dose_unit = fields.Selection([
        ('comprime', 'tablet(s)'),
        ('gelule', 'capsule(s)'),
        ('sachet', 'sachet(s)'),
        ('ml', 'ml'),
        ('mg', 'mg'),
        ('g', 'g'),
        ('goutte', 'drop(s)'),
        ('cac', 'teaspoon(s)'),
        ('cas', 'tablespoon(s)'),
        ('application', 'application(s)'),
        ('bain_bouche', 'mouthwash'),
        ('injection', 'injection(s)'),
        ('suppositoire', 'suppository(ies)'),
        ('ui', 'IU'),
    ], string="Dose unit")

    # --- Frequency: number of intakes + moment ---
    freq = fields.Selection([
        ('1j', 'once a day'),
        ('2j', 'twice a day'),
        ('3j', '3 times a day'),
        ('4j', '4 times a day'),
        ('4h', 'every 4 hours'),
        ('6h', 'every 6 hours'),
        ('8h', 'every 8 hours'),
        ('12h', 'every 12 hours'),
        ('48h', 'every 48 hours'),
        ('1s', 'once a week'),
        ('unique', 'single dose'),
        ('besoin', 'as needed'),
        ('douleur', 'in case of pain'),
    ], string="Frequency")
    moment = fields.Selection([
        ('avant_repas', 'before meals'),
        ('pendant_repas', 'with meals'),
        ('apres_repas', 'after meals'),
        ('matin', 'in the morning'),
        ('midi', 'at noon'),
        ('soir', 'in the evening'),
        ('matin_soir', 'morning and evening'),
        ('coucher', 'at bedtime'),
        ('jeun', 'on an empty stomach'),
    ], string="Moment")

    # --- Duration: number + unit ---
    duration_qty = fields.Selection([
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
        ('6', '6'), ('7', '7'), ('8', '8'), ('10', '10'), ('12', '12'),
        ('14', '14'), ('15', '15'), ('21', '21'), ('30', '30'),
        ('45', '45'), ('60', '60'), ('90', '90'),
    ], string="Duration")
    duration_unit = fields.Selection([
        ('jour', 'day(s)'),
        ('semaine', 'week(s)'),
        ('mois', 'month(s)'),
    ], string="Duration unit", default='jour')

    # --- Instructions: route + instruction + free note ---
    route = fields.Selection([
        ('orale', 'oral route'),
        ('locale', 'local application'),
        ('bain_bouche', 'as mouthwash'),
        ('sublinguale', 'sublingual route'),
        ('im', 'intramuscular injection'),
    ], string="Route")
    instruction = fields.Selection([
        ('eau', 'swallow with a large glass of water'),
        ('pas_croquer', 'do not chew or crush'),
        ('recracher', 'do not swallow, spit out after use'),
        ('garder_bouche', 'keep in mouth 1 minute before spitting out'),
        ('zone', 'apply to the affected area'),
        ('pas_alcool', 'avoid alcohol during treatment'),
        ('pas_depasser', 'do not exceed the prescribed dose'),
        ('espacer', 'space doses at least 4 hours apart'),
        ('jusqu_bout', 'complete the full course of treatment'),
        ('estomac_plein', 'take with food (full stomach)'),
    ], string="Instruction")
    extra_note = fields.Char(string="Free note")

    # Champs texte reconstruits à partir des sélections : les rapports
    # d'impression (prescription_template, report_prescription_template,
    # prescription_letterhead_template) les lisent tels quels.
    dosage = fields.Char(string="Dosage", compute='_compute_display_fields')
    frequency = fields.Char(string="Frequency", compute='_compute_display_fields')
    duration = fields.Char(string="Duration", compute='_compute_display_fields')
    instructions = fields.Char(string="Instructions", compute='_compute_display_fields')

    def _sel_label(self, field_name):
        # Libellé traduit dans la langue de l'utilisateur courant
        self.ensure_one()
        value = self[field_name]
        if not value:
            return ''
        selection = self._fields[field_name]._description_selection(self.env)
        return dict(selection).get(value, '')

    @api.depends('dose_qty', 'dose_unit', 'freq', 'moment',
                 'duration_qty', 'duration_unit', 'route', 'instruction',
                 'extra_note')
    def _compute_display_fields(self):
        for rec in self:
            rec.dosage = " ".join(
                p for p in [rec.dose_qty, rec._sel_label('dose_unit')] if p)
            rec.frequency = ", ".join(
                p for p in [rec._sel_label('freq'), rec._sel_label('moment')] if p)
            rec.duration = " ".join(
                p for p in [rec.duration_qty, rec._sel_label('duration_unit')] if p)
            rec.instructions = " – ".join(
                p for p in [rec._sel_label('route'), rec._sel_label('instruction'),
                            rec.extra_note or ''] if p)
