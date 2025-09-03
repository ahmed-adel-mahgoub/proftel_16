# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class UserData(models.Model):
    _name = 'user.data'
    _description = 'user_data'

    name = fields.Char()
    employee_id = fields.Many2one('hr.employee')
    sender_id = fields.Char(related='employee_id.sender_id')
    department_id = fields.Char(related='employee_id.department_id.name',
                                string='Department', readonly=True)
    email = fields.Char(related='employee_id.work_email')
    company_id = fields.Many2one(
        related='employee_id.company_id',
        string='Company',
        readonly=True,
        store=True
    )
    android_id = fields.Char()
    fcm_token = fields.Char()
    platform = fields.Char()
    manufacturer = fields.Char()
    model = fields.Char()
    hms_token = fields.Char()
    apns = fields.Char()
    app_type = fields.Selection([('admin','Admin'),
                               ('user','User'),
                               ],tracking=True,
                              )
    password = fields.Char()
    company_schedule_id = fields.Many2one(
        'company.schedule'
    )
    @api.model
    def create(self, vals):
        # Get company_id from vals or from related employee
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