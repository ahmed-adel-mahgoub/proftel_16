from odoo import models, fields, api
from odoo.exceptions import UserError


class TaskCancellationWizard(models.TransientModel):
    _name = 'task.cancellation.wizard'
    _description = 'Task Cancellation Wizard'

    reason = fields.Text(string="Cancellation Reason")
    task_id = fields.Many2one('mobile_app', string="Task", required=True)

    def action_confirm_cancellation(self):
        """Only executed when Confirm button is clicked"""
        self.ensure_one()
        if not self.reason:
            raise UserError("Cancellation reason is required!")

        self.task_id.write({
            'status': 'cancel',
            'reason_cancel': self.reason,
            'cancel_date': fields.Datetime.now(),
            'is_task_cancel': True
        })

        if hasattr(self.task_id, 'task_history'):
            self.task_id.task_history('cancel', 'cancel')

        return {'type': 'ir.actions.act_window_close'}

