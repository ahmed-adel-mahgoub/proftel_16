from odoo import models, fields, api

class Task(models.Model):
    _inherit = 'project.task'

    member_ids = fields.Many2many(
        'hr.employee',
        string='Task Members',
        help="Employees assigned to this task"
    )
    notified_member_ids = fields.Many2many(
        'hr.employee',
        relation='task_notified_member_rel',
        string='Notified Members',
        help="Employees who have received notifications for this task"
    )
    sender_ids = fields.One2many(
        'hr.employee',
        'sender_id',
        string='Sender IDs',
        help="Unique sender IDs for employees"
    )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        # Notify websocket server about new tasks
        self.env['websocket.server'].notify_new_tasks(tasks)
        return tasks

    def write(self, vals):
        res = super().write(vals)
        if 'member_ids' in vals:
            self.env['websocket.server'].notify_updated_tasks(self)
        return res