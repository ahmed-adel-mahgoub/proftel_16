# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrackingSend(models.Model):
    _name = 'tracking.send'
    _description = 'Tracking of Sent Mobile App Assignments'

    mobile_app_id = fields.Many2one(
        'mobile_app',
        string='Mobile App Task',
        required=True,
        help="Reference to the original Mobile App task"
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        help="Employee assigned to the task"
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help="Department of the assigned employee"
    )
    sender_id = fields.Char(
        string='Sender ID',
        help="WebSocket sender ID for communication"
    )
    is_send = fields.Boolean(
        string='Sent Status',
        default=False,
        help="Indicates if the assignment has been sent to the employee"
    )

    @api.model
    def create_assignments_from_mobile_app(self):
        """Create tracking records for unsent mobile app employee assignments"""
        mobile_apps = self.env['mobile_app'].search([])

        for app in mobile_apps:
            for emp_line in app.emp_dep_id.filtered(lambda x: not x.is_send):
                existing = self.search([
                    ('mobile_app_id', '=', app.id),
                    ('employee_id', '=', emp_line.employees_id.id),
                    ('is_send', '=', False)
                ])

                if not existing:
                    self.create({
                        'mobile_app_id': app.id,
                        'employee_id': emp_line.employees_id.id,
                        'department_id': emp_line.department_id.id,
                        'sender_id': emp_line.sender_id,
                        'is_send': False
                    })

    def update_sent_status(self):
        """Update is_send status based on empline records"""
        for tracking in self:
            emp_line = self.env['empline'].search([
                ('emp_ids', '=', tracking.mobile_app_id.id),
                ('employees_id', '=', tracking.employee_id.id),
                ('sender_id', '=', tracking.sender_id)
            ], limit=1)

            if emp_line and emp_line.is_send:
                tracking.write({'is_send': True})
                # Optionally uncomment to delete when sent
                # tracking.unlink()

    @api.model
    def cron_update_assignments(self):
        """Scheduled action to update tracking records"""
        self.create_assignments_from_mobile_app()
        unsent_records = self.search([('is_send', '=', False)])
        unsent_records.update_sent_status()

        # Delete all sent records
        sent_records = self.search([('is_send', '=', True)])
        sent_records.unlink()