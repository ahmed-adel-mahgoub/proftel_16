# -*- coding: utf-8 -*-
# from addons.hw_drivers.main import manager
from email.policy import default

import requests
import json
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class checkAattendance(models.Model):
     _name = "check.attendance"
     _description = 'mob attendance'


     name = fields.Char()
     employee_id = fields.Many2one('hr.employee')
     employee_email = fields.Char(related= "employee_id.work_email")
     check_in= fields.Datetime()
     check_out= fields.Datetime()
     full_approval = fields.Boolean(compute='full_approval_action', search=True, store=True)
     hr_approval_check_in = fields.Integer(readonly=1, store=True)
     hr_approval_check_out = fields.Integer(default=0,readonly=1, store=True)
     manager_approval_check_in = fields.Integer(readonly=1, store=True)
     manager_approval_check_out = fields.Integer(default=0,readonly=1, store=True)
     is_mobile = fields.Boolean()
     check_in_map = fields.Text()
     x_in_note = fields.Text(string="check in note")
     x_out_note = fields.Text(string="check out note")
     check_out_map = fields.Text()
     update =fields.Boolean()
     is_send =fields.Boolean()
     hr_update_check_in =fields.Boolean()
     hr_update_check_out =fields.Boolean()
     manger_update_check_in =fields.Boolean()
     manger_update_check_out =fields.Boolean()
     employee_image = fields.Text()
     place_image = fields.Text()
     user_in_image= fields.Text()
     place_in_image= fields.Text()
     user_out_image= fields.Text()
     place_out_image= fields.Text()
     state_hr_in = fields.Selection([
          ('hr_approve_in','HR check IN'),
          ('hr_rejected_in','HR check IN'),
     ])
     state_hr_out = fields.Selection([

          ('hr_approve_out','HR Approve out'),
          ('hr_rejected_out','HR Rejected out'),
     ])
     state_manger_in = fields.Selection([
          ('manger_approve_in','Manger Approve check IN'),
          ('manger_rejected_in','Manger rejected check IN'),

     ])
     state_manger_out = fields.Selection([

          ('manger_approve_out','Manger Approve check out'),
          ('manger_rejected_out','Manger rejected check out'),
     ])
     bool_field =fields.Boolean()
     update_api = fields.Boolean()





     @api.depends('hr_approval_check_in','hr_approval_check_out','manager_approval_check_in','manager_approval_check_out')
     def full_approval_action(self):
          for rec in self:
          #       if rec.full_approval ==1 :
          #            rec.create_attendance_record()
          # if rec.manager_approval==1 and rec.hr_approval==1:
          #      rec.full_approval = 1
               rec.full_approval = (rec.hr_approval_check_in ==1
                                    and rec.hr_approval_check_out ==1
                                    and rec.manager_approval_check_in==1
                                    and rec.manager_approval_check_out==1)
               # rec.create_attendance_record()

     def create_attendance_record(self):
          for record in self:
               if record.check_in or record.check_out:

                    if record.full_approval:

                         # if record.check_in >= record.check_out:
                         #       raise ValidationError("Check In time must be before Check Out time.")

                         attendance_vals = {
                              'employee_id': record.employee_id.id,
                              'check_in': record.check_in,
                              'check_out': record.check_out,
                              'check_attendance_id': record.id,
                         }
                         self.env['hr.attendance'].create(attendance_vals)
                    # else:
                    #      raise ValidationError("Attendance record is not valid.")
                 #automated create attendance record

     def automated_create_attendance_record(self):
          attendees_ids =self.search([])
          for rec in attendees_ids:
                    if rec.check_in or rec.check_out:
                         # if rec.full_approval:
                         #      if rec.check_in >= rec.check_out:
                         #           raise ValidationError("Check In time must be before Check Out time.")

                              attendance_vals = {
                                   'employee_id': rec.employee_id.id,
                                   'check_in': rec.check_in,
                                   'check_out': rec.check_out,
                                   'check_attendance_id': rec.id,
                              }
                              self.env['hr.attendance'].create(attendance_vals)

     # search for record chick in
     @api.onchange('check_out')
     def _onchange_checkout_date(self):
          if self.check_out:
               # Get the date part of the checkout date
               checkout_day = self.check_out.date()
               # Search for check-in records in hr.attendance for the same day
               attendance_records = self.env['hr.attendance'].search([
                    ('check_in', '>=', f'{checkout_day} 00:00:00'),
                    ('check_in', '<=', f'{checkout_day} 23:59:59'),
                    ('employee_id', '=', self.employee_id.id)
               ])
               # If a check-in record exists, set the checkin_date field
               if attendance_records:
                    self.check_in = attendance_records[0].check_in  # You can choose how to handle multiple records
                    self.update = 1




     def action_update_attendance(self):
          if self.full_approval == 1 :
               if self.check_out and self.employee_id:
                    # Get the date part of the checkout date
                    checkout_day = self.check_out.date()
                    # Search for check-in records in hr.attendance for the same day and employee
                    attendance_records = self.env['hr.attendance'].search([
                         ('check_in', '>=', f'{checkout_day} 00:00:00'),
                         ('check_in', '<=', f'{checkout_day} 23:59:59'),
                         ('employee_id', '=', self.employee_id.id),

                    ])

                    # Update the checkout date in hr.attendance if a record is found
                    for attendance in attendance_records:
                         attendance.write({'check_out': self.check_out,
                                           'check_attendance_id': self.id,
                                           })
# hr approve and reject check in
     def hr_approval_check_in_action(self):
          for rec in self:
               if rec.hr_approval_check_in != 1:
                    rec.hr_approval_check_in = 1
                    rec.state_hr_in ='hr_approve_in'
     def hr_rejected_check_in_action(self):
          for rec in self:
               if rec.hr_approval_check_in != 2:
                    rec.hr_approval_check_in = 2
                    rec.state_hr_in = 'hr_rejected_in'
                    # hr approve and reject check out
     def hr_approval_check_out_action(self):
          for rec in self:
               if rec.hr_approval_check_out != 1:
                    rec.hr_approval_check_out = 1
                    rec.state_hr_out = 'hr_approve_out'

               if rec.update ==1:
                     rec.manager_approval_check_in = 1
                     rec.hr_approval_check_in = 1

     def hr_rejected_check_out_action(self):
          for rec in self:
               if rec.hr_approval_check_out != 2:
                    rec.hr_approval_check_out = 2
                    rec.state_hr_out = 'hr_rejected_out'

     # manager approve and reject check in
     def manger_approval_check_in_action(self):
          for rec in self:
               if rec.manager_approval_check_in != 1:
                    rec.manager_approval_check_in = 1
                    rec.state_manger_in = 'manger_approve_in'
     def manger_rejected_check_in_action(self):
          for rec in self:
               if rec.manager_approval_check_in != 2:
                    rec.manager_approval_check_in = 2
                    rec.state_manger_in = 'manger_rejected_in'
                    # if rec.hr_approval == 1:
                    #       rec.create_attendance_record()
               # manager rejected and reject check out
     def manger_approval_check_out_action(self):
          for rec in self:
               if rec.manager_approval_check_out != 1:
                    rec.manager_approval_check_out = 1
                    rec.state_manger_out = 'manger_approve_out'
               if rec.update == 1:
                    rec.manager_approval_check_in = 1
                    rec.hr_approval_check_in = 1
     def manger_rejected_check_out_action(self):
          for rec in self:
               if rec.manager_approval_check_out != 2:
                    rec.manager_approval_check_out = 2
                    rec.state_manger_out = 'manger_rejected_out'

     @api.model
     def get_data_from_api(self, _logger=None):
          url = "http://www.proftelgroup.com/api/update_records"

          try:
               response = requests.get(url)
               response.raise_for_status()  # Raise an error for bad responses
               data = response.json()  # Parse the JSON response
               print(data)
               # return data  # Return the data or process it as needed
               # Assuming the data is a list of dictionaries
               for item in data:
                    self.create({
                         'name': item.get('name'),

                    })
               return True  # Indicate success
          except requests.exceptions.RequestException as e:
               # Handle exceptions (e.g., log the error)
               _logger.error(f"Error fetching data from API: {e}")
               return None

