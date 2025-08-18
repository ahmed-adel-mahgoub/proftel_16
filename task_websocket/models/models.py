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
        for task in tasks:
            self.env['websocket.server'].notify_task_update(task, 'create')
        return tasks

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in
               ['name', 'description', 'stage_id', 'member_ids']):
            for task in self:
                self.env['websocket.server'].notify_task_update(task, 'update')
        return res