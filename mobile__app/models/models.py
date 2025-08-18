# -*- coding: utf-8 -*-

from odoo.release import version
odoo_version = version
import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api,_
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import pytz





class mobile_app(models.Model):
    _name = 'mobile_app'
    _description = 'mobile_app'
    _inherit = ['mail.thread','mail.activity.mixin']

    # , 'calendar.recurrence'

    name = fields.Char(tracking=True)
    task_name = fields.Char(tracking=True)
    status_id = fields.Integer(tracking=True)
    task_type = fields.Char(tracking=True)
    reminder = fields.Integer(tracking=True)
    address = fields.Char(tracking=True)
    location = fields.Char(tracking=True)

    #dates
    duration=fields.Float(string='Duration', compute='_compute_hours_difference')
    average_time = fields.Float(string='Average', compute='_compute_average_difference')
    done_date = fields.Datetime(string="Done Date", tracking=True,readonly=1)
    in_progress_date = fields.Datetime(string="Start Date ", tracking=True,readonly=1)
    cancel_date = fields.Datetime(string="Cancel Date", tracking=True,readonly=1)
    estimated_date = fields.Datetime(string="Estimated Date", tracking=True)
    reason_cancel = fields.Text(string="Reason of Cancellation", tracking=True)
    description = fields.Text(string="Description", tracking=True)
    is_task_location =fields.Boolean(tracking=True,string="Is Task Related To Location")
    is_task_zone = fields.Boolean(tracking=True,string="Is Task Related To Zone")
    employees_id=fields.Many2many("hr.employee", string="Task Members")
    project_id = fields.Many2one("project.project")
    domain = [('department_ids', '=', 1), ('active', '=', True)]
    #emp_line id
    emp_dep_id=fields.One2many('empline','emp_ids')
    #new department field

    department_id = fields.Many2many("hr.department", string="Privacy")
    kind_id= fields.Many2one('kind',string="kind")
    status = fields.Selection([('pending','Pending'),
                               ('in_progress','In Progress'),
                               ('done','Done'),
                              ('cancel','Cancel'),
                             ('failed','Failed')],tracking=True,
                              default='pending'
                              )
    related_task=fields.Many2one('mobile_app',string="Related Task")

    sync = fields.Boolean(readonly=True)

    type_id = fields.Many2one('type', string="Type")
    #contact
    is_task_contact=fields.Boolean(string="Is Task Related to Contact")
    company_type_id =fields.Many2one('company.type')
    contact_id=fields.Many2one('res.partner',string="Contact")
    contact_street = fields.Char(related='contact_id.street')
    contact_street2 = fields.Char(related='contact_id.street2')
    contact_city = fields.Char(related='contact_id.city')
    contact_zip = fields.Char(related='contact_id.zip')
    contact_child_ids = fields.One2many(related='contact_id.child_ids')
    #server time
    coming_time =fields.Datetime(string="APP Coming Time",readonly=1)
    priority = fields.Selection([('0', 'Normal'),('1', 'low'), ('2', 'mid'), ('3', 'high')], default='0', string="Priority",)
    #------------------------
    alarm_ids=fields.Many2many('calendar.alarm',string="Reminders")
    order_by_id = fields.Many2one("hr.employee", string="Order By",domain =[('is_manger', '=', True)])
    domain =[('order_by_id.is_manger', '=', True)]
    starting_at=fields.Datetime(readonly=0)
    ending_at=fields.Datetime()
    note=fields.Text()
    activity_id=fields.Many2one('mail.activity')
    reply_activity_id = fields.Many2one('mail.reply.activity', string='Reply Activity')
    #cancel action
    is_task_cancel=fields.Boolean()
    reschedule_time=fields.Datetime()
    reschedule_type_id=fields.Many2one('reschedule.type')
    #renew reason
    renew_reason = fields.Char()
    is_task_renew = fields.Boolean()
    renew_state=fields.Selection({
        ('renew','renew')
    })

    websocket_client_id = fields.Many2many(
        'websocket.clients',
        string='WebSocket Clients',
        domain="[('is_active', '=', True)]"
    )

    sender_id = fields.Char(
        string='Sender IDs',
        compute='_compute_sender_ids',
        help="Comma-separated list of sender IDs for WebSocket communications"
    )

    @api.depends('websocket_client_id')
    def _compute_sender_ids(self):
        for record in self:
            record.sender_id = ', '.join(record.websocket_client_id.mapped('sender_id'))


    @api.model

    def _write(self, vals):
        rec = super(mobile_app,self)._write(vals)
        for rec in self:
            if rec.sync==False:
                rec.sync = True
    def renew_action(self):
        for rec in self:
            rec.task_history(rec.status, 'pinding')
            rec.status='pending'
            rec.renew_state='renew'
            rec.starting_at = fields.Datetime.now()
            return rec.status
            if rec.is_task_renew == False:
                rec.is_task_renew = True
    def done_action(self):
        for rec in self:
            rec.task_history(rec.status, 'done')
            rec.status='done'
            rec.done_date = fields.Datetime.now()
            return rec.status

    def failed_action(self):
        for rec in self:
            rec.task_history(rec.status, 'failed')
            rec.status='failed'

            return rec.status

    def in_progress_action(self):
        for rec in self:
            rec.task_history(rec.status, 'in_progress')
            rec.status='in_progress'
            rec.in_progress_date = fields.Datetime.now()
            return rec.status

    def cancel_action(self):
        self.ensure_one()

        return {
            'name': 'Enter Cancellation Reason',
            'type': 'ir.actions.act_window',
            'res_model': 'task.cancellation.wizard',  # Must match your wizard's _name
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_task_id': self.id,
                'default_status': 'cancel'  # Pass status as context if needed
            },
        }
    # define task history function
    def task_history(self,old_state,new_state):
        for rec in (self):
            rec.env["task.history"].create(
                {
                    'user_id': rec.env.uid,
                    'task_id': rec.id,
                    'old_state':old_state,
                    'new_state':new_state,
                    'date':fields.Datetime.now(),

                }
            )



    @api.depends('starting_at', 'cancel_date','done_date')
    def _compute_hours_difference(self):
        for record in self:
            if record.starting_at and record.cancel_date:
                diff = relativedelta(record.cancel_date, record.starting_at)
                record.duration = diff.hours + diff.days * 24
            elif record.starting_at and record.done_date:
                diff = relativedelta(record.done_date, record.starting_at)
                record.duration = diff.hours + diff.days * 24
            else:
                record.duration = 0



    @api.depends('starting_at', 'ending_at')
    def _compute_average_difference(self):
        for record in self:
            if record.starting_at and record.ending_at:
                diff = relativedelta(record.ending_at, record.starting_at)
                record.average_time = (diff.hours + diff.days * 24)/2
            else:
                record.average_time = 0
    #new  -----
    # def action_send_via_websocket(self):
    #     self.ensure_one()
    #     if not self.websocket_client_id:
    #         raise UserError("No WebSocket client configured")
    #
    #     # Prepare message
    #     message = {
    #         "action": "listen_attendance",
    #         "data": [{
    #             "name": self.name,
    #             "description": self.description,
    #             "duration": self.duration,
    #
    #         }]
    #     }
    #
    #     try:
    #         success = self.websocket_client_id.send_message_to_client(
    #             self.websocket_client_id.client_id,
    #             message
    #         )
    #         if success:
    #             return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': 'Success',
    #                     'message': f"Message sent to {self.websocket_client_id.client_id}",
    #                     'type': 'success',
    #                     'sticky': False,
    #                 }
    #             }
    #         raise UserError("Delivery failed (no acknowledgement received)")
    #     except Exception as e:
    #         raise UserError(f"Delivery failed: {str(e)}")
    def action_send_via_websocket(self):
        self.ensure_one()
        if not self.websocket_client_id:
            raise UserError("No active WebSocket clients configured")

        # Prepare base message
        base_message = {
            "action": "listen_attendance",
            "data": [{
                "name": self.name,
                "description": self.description,
                "duration": self.duration,
            }]
        }

        failed_clients = []
        successful_clients = []

        for client in self.websocket_client_id:
            try:
                # Create client-specific message with sender_id
                client_message = base_message.copy()
                client_message['sender_id'] = client.sender_id  # Include the specific sender_id

                success = client.send_message_to_client(
                    client.client_id,
                    client_message
                )

                if success:
                    successful_clients.append(f"{client.client_id} (Sender: {client.sender_id})")
                    empline_records = self.env['empline'].search([
                        ('emp_ids', '=', self.id),
                        ('sender_id', '=', client.sender_id)
                    ])
                    empline_records.write({'is_send': True})
                else:
                    failed_clients.append(f"{client.client_id} (Sender: {client.sender_id})")
            except Exception as e:
                failed_clients.append(f"{client.client_id} (Sender: {client.sender_id}) - Error: {str(e)}")

        if failed_clients and successful_clients:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Partial Success',
                    'message': f"Sent to {len(successful_clients)} clients. Failed for: {', '.join(failed_clients)}",
                    'type': 'warning',
                    'sticky': True,  # Make sticky so user can see all details
                }
            }
        elif failed_clients:
            raise UserError(f"Delivery failed to all clients:\n{''.join(failed_clients)}")
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f"Message sent to {len(successful_clients)} clients:\n{''.join(successful_clients)}",
                    'type': 'success',
                    'sticky': True,
                }
            }

class empline(models.Model):
    _name='empline'
    emp_ids =fields.Many2one('mobile_app')
    department_id = fields.Many2one("hr.department", string="Privacy")
    employees_id = fields.Many2one("hr.employee", string="Task Members")
    sender_id = fields.Char(related="employees_id.sender_id")
    is_send = fields.Boolean()
class mail_reply_log(models.Model):
    _name = 'mail.reply.log'
    mail_message_id =fields.Many2one('mail.message',required=1)
    parent_id = fields.Many2one('mail.reply.log')
    message =fields.Text()
    author_id = fields.Many2one('res.users')
    active=fields.Boolean(default=1)

    @api.model
    def message_post(self, **kwargs):
        result = super().message_post(**kwargs)
        reply_text = kwargs.get('body')
        if reply_text:
            reply_log = self.env['mail.reply.log'].create({
                'mail_message_id': result.id,
                'message': reply_text,
                'author_id': self.env.user.id,
            })
        return

