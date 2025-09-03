from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)


class CompanySubscription(models.Model):
    _name = 'company.subscription'
    _description = 'Company Subscription'

    company_id = fields.Many2one('res.company', string='Company', required=True)
    date_from = fields.Date(string='Start Date', required=True,
                            default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True)
    is_active = fields.Boolean(string='Active', compute='_compute_is_active',
                               store=True)
    modules_rules_ids = fields.Many2many('modules.rules')
    no_of_user = fields.Integer(required=True, default=1)

    @api.depends('date_from', 'date_to')
    def _compute_is_active(self):
        today = fields.Date.today()
        for sub in self:
            if sub.date_from and sub.date_to:
                sub.is_active = sub.date_from <= today <= sub.date_to
            else:
                sub.is_active = False

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for sub in self:
            if sub.date_from and sub.date_to and sub.date_to < sub.date_from:
                raise ValidationError("End date must be after start date")

    @api.constrains('no_of_user')
    def _check_user_positive(self):
        """Only check that the number is positive, not the actual count"""
        for subscription in self:
            if subscription.no_of_user <= 0:
                raise ValidationError("Number of users must be greater than 0")

    def write(self, vals):
        """Override write method to validate user count when decreasing no_of_user"""
        if 'no_of_user' in vals:
            # Check if we're decreasing the number of users
            for subscription in self:
                current_no_of_user = subscription.no_of_user
                new_no_of_user = vals['no_of_user']

                if new_no_of_user < current_no_of_user:
                    # Get current user count for the company
                    user_count = self.env['user.data'].search_count([
                        ('company_id', '=', subscription.company_id.id)
                    ])

                    if user_count > new_no_of_user:
                        raise ValidationError(
                            f"Cannot reduce number of users to {new_no_of_user}. "
                            f"Company {subscription.company_id.name} currently has {user_count} users "
                            f"which exceeds the new limit. You must first remove some users or "
                            f"consider creating a database backup before making this change."
                        )

        return super(CompanySubscription, self).write(vals)

    def cron_check_subscriptions(self):
        """ Scheduled action to deactivate expired subscriptions """
        today = fields.Date.today()
        expired = self.search([
            ('date_to', '<', today),
            ('is_active', '=', True)
        ])
        expired.write({'is_active': False})

    def action_check_user_limits(self):
        """Manual action to check user limits (can be called from UI if needed)"""
        for subscription in self:
            if subscription.is_active:
                user_count = self.env['user.data'].search_count([
                    ('company_id', '=', subscription.company_id.id)
                ])
                if user_count > subscription.no_of_user:

                    _logger.warning(
                        "Company %s has %s users which exceeds the subscription limit of %s users.",
                        subscription.company_id.name, user_count,
                        subscription.no_of_user
                    )