from odoo import api, fields, models


class AccessManage(models.Model):
    _name = 'access.manage'
    _description = 'Access Manage'

    name = fields.Char(string='Name', required=True)
    email = fields.Char(string='Email')
    phone_number = fields.Char(string='Phone Number')
    password = fields.Char(string='Password')
    group_list = fields.Many2many(
        'res.groups',
        string='Groups',
        domain=[('name', 'in', ['CEO', 'ADMIN', 'RECEPTION', 'DOCTOR', 'SALESPERSON'])],
    )
    user_id = fields.Many2one('res.users', string='Linked User', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        internal_user_group = self.env.ref('base.group_user')
        for record, vals in zip(records, vals_list):
            if vals.get('user_id'):
                # already linked to an existing real user (e.g. via the sync action), don't create a new one
                continue
            user = self.env['res.users'].create({
                'name': record.name,
                'login': record.email,
                'email': record.email,
                'phone': record.phone_number,
                'password': record.password,
                'group_ids': [(6, 0, (record.group_list | internal_user_group).ids)],
            })
            record.user_id = user
        return records

    def write(self, vals):
        res = super().write(vals)
        internal_user_group = self.env.ref('base.group_user')
        for record in self:
            if not record.user_id:
                continue
            user_vals = {}
            if 'name' in vals:
                user_vals['name'] = record.name
            if 'email' in vals:
                user_vals['login'] = record.email
                user_vals['email'] = record.email
            if 'phone_number' in vals:
                user_vals['phone'] = record.phone_number
            if 'password' in vals:
                user_vals['password'] = record.password
            if 'group_list' in vals:
                user_vals['group_ids'] = [(6, 0, (record.group_list | internal_user_group).ids)]
            if user_vals:
                record.user_id.write(user_vals)
        return res

    def unlink(self):
        users = self.mapped('user_id')
        res = super().unlink()
        users.unlink()
        return res

    def action_sync_missing_users(self):
        linked_records = self.search([('user_id', '!=', False)])
        record_by_user = {record.user_id.id: record for record in linked_records}
        known_groups = self.env['res.groups'].search([
            ('name', 'in', ['CEO', 'ADMIN', 'RECEPTION', 'DOCTOR', 'SALESPERSON']),
        ])
        all_users = self.env['res.users'].search([('share', '=', False)])

        create_vals_list = []
        for user in all_users:
            expected_groups = user.group_ids & known_groups
            record = record_by_user.get(user.id)
            if record:
                update_vals = {}
                if record.name != user.name:
                    update_vals['name'] = user.name
                if record.email != user.login:
                    update_vals['email'] = user.login
                if record.phone_number != user.phone:
                    update_vals['phone_number'] = user.phone
                if set(record.group_list.ids) != set(expected_groups.ids):
                    update_vals['group_list'] = [(6, 0, expected_groups.ids)]
                if update_vals:
                    record.write(update_vals)
            else:
                create_vals_list.append({
                    'name': user.name,
                    'email': user.login,
                    'phone_number': user.phone,
                    'group_list': [(6, 0, expected_groups.ids)],
                    'user_id': user.id,
                })
        if create_vals_list:
            self.create(create_vals_list)
