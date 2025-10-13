# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UserData(models.Model):
    _name = 'user.data'
    _description = 'user_data'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee')
    sender_id = fields.Char(related='employee_id.sender_id')

    company_id = fields.Many2one(
        'res.company',
        string='company',
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
    )
    email = fields.Char(related='employee_id.work_email')

    android_id = fields.Char()
    fcm_token = fields.Char()
    platform = fields.Char()
    manufacturer = fields.Char()
    model = fields.Char()
    hms_token = fields.Char()
    apns = fields.Char()
    admin = fields.Boolean()
    user = fields.Boolean()
    company_schedule_id = fields.Many2one(
        'company.schedule'
    )
    user_name = fields.Char("User Name")
    password = fields.Char("Password")

    has_user_name = fields.Boolean(
        compute='_compute_has_user_name',
        string='Has User Name'
    )

    @api.depends('employee_id')
    def _compute_has_user_name(self):
        for record in self:
            if record.employee_id:

                employee_user = self.env['res.users'].search([
                    ('partner_id', '=', record.employee_id.user_partner_id.id)
                ], limit=1)
                record.has_user_name = bool(
                    employee_user and employee_user.login)
            else:
                record.has_user_name = False

    @api.onchange('employee_id')
    def _onchange_employee_id(self):

        for record in self:
            if record.employee_id:

                employee_user = self.env['res.users'].search([
                    ('partner_id', '=', record.employee_id.user_partner_id.id)
                ], limit=1)

                if employee_user and employee_user.login:
                    record.user_name = employee_user.login

                else:

                    record.user_name = False

    @api.model
    def create(self, vals):

        company_id = vals.get('company_id')
        if not company_id and vals.get('employee_id'):
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            company_id = employee.company_id.id
            vals['company_id'] = company_id

        if company_id:
            subscription = self.env['company.subscription'].search([
                ('company_id', '=', company_id),
                ('is_active', '=', True)
            ], limit=1)
            if not subscription:
                raise ValidationError(
                    "Cannot create new user. Company %s does not have an active subscription." %
                    self.env['res.company'].browse(company_id).name
                )

            if subscription:
                user_count = self.search_count(
                    [('company_id', '=', company_id)])

                if user_count >= subscription.no_of_user:
                    raise ValidationError(
                        "Cannot create new user. Company %s has reached its subscription limit of %s users." %
                        (subscription.company_id.name, subscription.no_of_user)
                    )

        return super(UserData, self).create(vals)

    def action_create_user(self):
        for rec in self:
            if not rec.user_name:
                raise ValidationError("User name is required.")

            if not rec.has_user_name and not rec.password:
                raise ValidationError("Password is required for new users.")

            if not rec.has_user_name:
                existing = self.env['res.users'].search(
                    [('login', '=', rec.user_name)], limit=1)
                if existing:
                    raise ValidationError(
                        "User with this login already exists.")

            if rec.has_user_name:
                user = self.env['res.users'].search([
                    ('login', '=', rec.user_name)
                ], limit=1)
                if not user:
                    raise ValidationError("Existing user not found.")
            else:
                user = self.env['res.users'].create({
                    'name': rec.user_name,
                    'login': rec.user_name,
                    'password': rec.password,
                })
            return user