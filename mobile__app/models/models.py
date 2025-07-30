# -*- coding: utf-8 -*-

from odoo.release import version

odoo_version = version
from calendar import calendar
from datetime import timedelta
from itertools import repeat
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
import websockets
import asyncio
import json
import logging
_logger = logging.getLogger(__name__)

import math
import uuid
from odoo import models, fields, api,_
from odoo.exceptions import UserError
from odoo.tools.view_validation import READONLY
from dateutil.relativedelta import relativedelta
import pytz
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.calendar.models.calendar_recurrence import (
    weekday_to_field,
    RRULE_TYPE_SELECTION,
    END_TYPE_SELECTION,
    MONTH_BY_SELECTION,
    WEEKDAY_SELECTION,
    BYDAY_SELECTION
)

def get_weekday_occurence(date):
    """
    :returns: ocurrence

    >>> get_weekday_occurence(date(2019, 12, 17))
    3  # third Tuesday of the month

    >>> get_weekday_occurence(date(2019, 12, 25))
    -1  # last Friday of the month
    """
    occurence_in_month = math.ceil(date.day/7)
    if occurence_in_month in {4, 5}:  # fourth or fifth week on the month -> last
        return -1
    return occurence_in_month


class mobile_app(models.Model):
    _name = 'mobile_app'
    _description = 'mobile_app'
    _inherit = ['mail.thread','mail.activity.mixin']

    # , 'calendar.recurrence'

    name = fields.Char(tracking=True)

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
    kind= fields.Selection([('1','Internal'),('2','Client')] ,tracking=True)
    status = fields.Selection([('pending','Pending'),('in_progress','In Progress'),('done','Done'),('cancel','Cancel'),('failed','Failed')],tracking=True,default='pending')
    related_task=fields.Many2one('mobile_app',string="Related Task")

    sync = fields.Boolean(readonly=True)

    type_id = fields.Many2one('type', string="Type")
    #contact
    is_task_contact=fields.Boolean(string="Is Task Related to Contact")
    company_type =fields.Selection([('individual','Individual'),('company','Company')])
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
    reschedule_type=fields.Selection([('from_start_date','from start date'),('from_end_date','from end date')])
    #renew reason
    renew_reason = fields.Char()
    is_task_renew = fields.Boolean()
    renew_state=fields.Selection({
        ('renew','renew')
    })
    # new fields websockets
    # websocket_client_id = fields.Many2one(
    #     'websocket.clients',
    #     string='WebSocket Client',
    #     domain="[('is_active', '=', True)]"
    # )
    # sender_id = fields.Char(
    #     string='Sender ID',
    #     help="The ID used to identify this record in WebSocket communications",
    #     related="websocket_client_id.sender_id"
    # )
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
#-----------------------------------------------------------------------------------------
    # RECURRENCE FIELD
    recurrency = fields.Boolean('Recurrent')
    recurrence_id = fields.Many2one(
        'calendar.recurrence', string="Recurrence Rule")
    follow_recurrence = fields.Boolean(
        default=False)  # Indicates if an event follows the recurrence, i.e. is not an exception
    recurrence_update = fields.Selection([
        ('self_only', "This event"),
        ('future_events', "This and following events"),
        ('all_events', "All events"),
    ], store=False, copy=False, default='self_only',
        help="Choose what to do with other events in the recurrence. Updating All Events is not allowed when dates or time is modified")
    # Those field are pseudo-related fields of recurrence_id.
    # They can't be "real" related fields because it should work at record creation
    # when recurrence_id is not created yet.
    # If some of these fields are set and recurrence_id does not exists,
    # a `calendar.recurrence.rule` will be dynamically created.
    rrule = fields.Char('Recurrent Rule', compute='_compute_recurrence', readonly=False)
    rrule_type = fields.Selection(RRULE_TYPE_SELECTION, string='Recurrence',
                                  help="Let the event automatically repeat at that interval",
                                  compute='_compute_recurrence', readonly=False)
    event_tz = fields.Selection(
        _tz_get, string='Timezone', compute='_compute_recurrence', readonly=False)
    end_type = fields.Selection(
        END_TYPE_SELECTION, string='Recurrence Termination',
        compute='_compute_recurrence', readonly=False)
    interval = fields.Integer(
        string='Repeat Every', compute='_compute_recurrence', readonly=False,
        help="Repeat every (Days/Week/Month/Year)")
    count = fields.Integer(
        string='Repeat', help="Repeat x times", compute='_compute_recurrence', readonly=False)
    mon = fields.Boolean(compute='_compute_recurrence', readonly=False)
    tue = fields.Boolean(compute='_compute_recurrence', readonly=False)
    wed = fields.Boolean(compute='_compute_recurrence', readonly=False)
    thu = fields.Boolean(compute='_compute_recurrence', readonly=False)
    fri = fields.Boolean(compute='_compute_recurrence', readonly=False)
    sat = fields.Boolean(compute='_compute_recurrence', readonly=False)
    sun = fields.Boolean(compute='_compute_recurrence', readonly=False)
    month_by = fields.Selection(
        MONTH_BY_SELECTION, string='Option', compute='_compute_recurrence', readonly=False)
    day = fields.Integer('Date of month', compute='_compute_recurrence', readonly=False)
    weekday = fields.Selection(WEEKDAY_SELECTION, compute='_compute_recurrence', readonly=False)
    byday = fields.Selection(BYDAY_SELECTION, string="By day", compute='_compute_recurrence', readonly=False)
    until = fields.Date(compute='_compute_recurrence', readonly=False)
    # UI Fields.
    display_description = fields.Boolean(compute='_compute_display_description')
    privacy = fields.Selection(
        [('public', 'Public'),
         ('private', 'Private'),
         ('confidential', 'Only internal users')],
        'Privacy', default='public', required=True,
        help="People to whom this event will be visible.")
    show_as = fields.Selection(
        [('free', 'Available'),
         ('busy', 'Busy')], 'Show as', default='busy', required=True,
        help="If the time is shown as 'busy', this event will be visible to other people with either the full \
            information or simply 'busy' written depending on its privacy. Use this option to let other people know \
            that you are unavailable during that period of time. \n If the event is shown as 'free', other users know \
            that you are available during that period of time.")
    start = fields.Datetime(
        'Start', required=True, tracking=True, default=fields.Date.today,
        help="Start date of an event, without time for full days events")
    allday = fields.Boolean('All Day', default=False)
    @api.depends('recurrence_id', 'recurrency')
    def _compute_recurrence(self):
        recurrence_fields = self._get_recurrent_fields()
        false_values = {field: False for field in recurrence_fields}  # computes need to set a value
        defaults = self.env['calendar.recurrence'].default_get(recurrence_fields)
        default_rrule_values = self.recurrence_id.default_get(recurrence_fields)
        for event in self:
            if event.recurrency:
                event.update(
                    defaults)  # default recurrence values are needed to correctly compute the recurrence params
                event_values = event._get_recurrence_params()
                rrule_values = {
                    field: event.recurrence_id[field]
                    for field in recurrence_fields
                    if event.recurrence_id[field]
                }
                rrule_values = rrule_values or default_rrule_values
                event.update({**false_values, **defaults, **event_values, **rrule_values})
            else:
                event.update(false_values)



    @api.model
    def _get_recurrent_fields(self):
        return {'byday', 'until', 'rrule_type', 'month_by', 'event_tz', 'rrule',
                'interval', 'count', 'end_type', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat',
                'sun', 'day', 'weekday'}

    def _get_recurrence_params(self):
        if not self:
            return {}
        event_date = self._get_start_date()
        weekday_field_name = weekday_to_field(event_date.weekday())
        return {
            weekday_field_name: True,
            'weekday': weekday_field_name.upper(),
            'byday': str(get_weekday_occurence(event_date)),
            'day': event_date.day,
        }
    def _get_start_date(self):
        """Return the event starting date in the event's timezone.
        If no starting time is assigned (yet), return today as default
        :return: date
        """
        if not self.start:
            return fields.Date.today()
        if self.recurrency and self.event_tz:
            tz = pytz.timezone(self.event_tz)
            # Ensure that all day events date are not calculated around midnight. TZ shift would potentially return bad date
            start = self.start if not self.allday else self.start.replace(hour=12)
            return pytz.utc.localize(start).astimezone(tz).date()
        return self.start.date()


    def _split_recurrence(self, time_values):
        """Apply time changes to events and update the recurrence accordingly.

        :return: detached events
        """
        self.ensure_one()
        if not time_values:
            return self.browse()
        if self.follow_recurrence and self.recurrency:
            previous_week_day_field = weekday_to_field(self._get_start_date().weekday())
        else:
            # When we try to change recurrence values of an event not following the recurrence, we get the parameters from
            # the base_event
            previous_week_day_field = weekday_to_field(self.recurrence_id.base_event_id._get_start_date().weekday())
        self.write(time_values)
        return self._apply_recurrence_values({
            previous_week_day_field: False,
            **self._get_recurrence_params(),
        }, future=True)

    @api.model
    def _get_recurrence_params_by_date(self, event_date):
        """ Return the recurrence parameters from a date object. """
        weekday_field_name = weekday_to_field(event_date.weekday())
        return {
            weekday_field_name: True,
            'weekday': weekday_field_name.upper(),
            'byday': str(get_weekday_occurence(event_date)),
            'day': event_date.day,
        }

    def _break_recurrence(self, future=True):
        """Breaks the event's recurrence.
        Stop the recurrence at the current event if `future` is True, leaving past events in the recurrence.
        If `future` is False, all events in the recurrence are detached and the recurrence itself is unlinked.
        :return: detached events excluding the current events
        """
        recurrences_to_unlink = self.env['calendar.recurrence']
        detached_events = self.env['calendar.event']
        for event in self:
            recurrence = event.recurrence_id
            if future:
                detached_events |= recurrence._stop_at(event)
            else:
                detached_events |= recurrence.calendar_event_ids
                recurrence.calendar_event_ids.recurrence_id = False
                recurrences_to_unlink |= recurrence
        recurrences_to_unlink.with_context(archive_on_error=True).unlink()
        return detached_events - self
    #-----------------------------------------------------------------------------------

    # day = fields.Many2many('calendar.weekday', string='Days', default=[(6, False)])
    # recurrency=fields.Boolean()
    @api.model
    #mob sync
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
        self.ensure_one()  # Ensures this is called on a single record
        # self.status = 'cancel'
        # Return wizard popup without changing status first
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

