from odoo import models, fields, api
from odoo.exceptions import UserError

class RadiusEntry(models.Model):
    _name = 'radius.entry'
    _description = 'RADIUS Entry'

    company_id = fields.Many2one('res.partner', string='Company', domain=[('is_company','=',True)])
    project_id = fields.Many2one('project.project', string='Project')
    event_id = fields.Many2one('event.event', string='Event')

    first_name = fields.Char('First Name', required=True)
    last_name = fields.Char('Last Name', required=True)

    radius_username = fields.Char('Username', required=True, index=True)
    radius_password = fields.Char('Password', required=True)
    start_time = fields.Datetime('Start Time', required=True, default=fields.Datetime.now)
    end_time = fields.Datetime('End Time', required=True)
    active = fields.Boolean('Active', default=True)

    created_at = fields.Datetime('Created At', default=lambda self: fields.Datetime.now())

    def action_push_to_radius(self):
        self.ensure_one()
        now = fields.Datetime.now()
        if not (self.start_time <= now <= self.end_time):
            raise UserError('Current time is outside the allowed range.')
        query = """
INSERT INTO radcheck (username, attribute, op, value)
VALUES (%s, 'Cleartext-Password', ':=', %s)
ON CONFLICT (username) DO UPDATE SET value = EXCLUDED.value;
"""
        try:
            self.env.cr.execute(query, (self.radius_username, self.radius_password))
        except Exception as e:
            raise UserError('Failed to write to radcheck table: %s' % e)

    @api.model
    def _cron_cleanup_expired(self):
        now = fields.Datetime.now()
        expired = self.search([('end_time','<', now), ('active','=',True)])
        for rec in expired:
            try:
                self.env.cr.execute('DELETE FROM radcheck WHERE username=%s', (rec.radius_username,))
            except Exception:
                pass
            rec.active = False
