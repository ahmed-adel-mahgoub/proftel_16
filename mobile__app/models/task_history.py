# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TaskHistory(models.Model):
    _name = 'task.history'


    user_id = fields.Many2one("res.users")
    task_id = fields.Many2one("mobile_app")
    old_state=fields.Char()
    new_state = fields.Char()
    date= fields.Datetime()












