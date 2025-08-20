from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date

class CompanySubscription(models.Model):
    _name = 'company.subscription'
    _description = 'Company Subscription'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True)
    is_active = fields.Boolean(string='Active', compute='_compute_is_active', store=True)


    @api.depends('date_from', 'date_to')
    def _compute_is_active(self):
        today = fields.Date.today()
        for sub in self:
            if sub.date_from and sub.date_to:  # Check if dates are set
                sub.is_active = sub.date_from <= today <= sub.date_to
            else:
                sub.is_active = False

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for sub in self:
            if sub.date_from and sub.date_to and sub.date_to < sub.date_from:
                raise ValidationError("End date must be after start date")

    def cron_check_subscriptions(self):
        """ Scheduled action to deactivate expired subscriptions """
        today = fields.Date.today()
        expired = self.search([
            ('date_to', '<', today),
            ('is_active', '=', True)
        ])
        expired.write({'is_active': False})