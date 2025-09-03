from odoo import models, fields

class RadiusRequest(models.Model):
    _name = 'radius.request'
    _description = 'RADIUS Request'
    _order = 'date_requested desc'

    company_id = fields.Many2one('res.partner', string='Company')
    project_id = fields.Many2one('project.project', string='Project')
    event_id = fields.Many2one('event.event', string='Event')

    request_type = fields.Selection([('create','Create'),('update','Update'),('delete','Delete')], string='Request Type', default='create')
    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user)
    date_requested = fields.Datetime('Date Requested', default=fields.Datetime.now)
    state = fields.Selection([('draft','Draft'),('approved','Approved'),('rejected','Rejected')], string='Status', default='draft')

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
