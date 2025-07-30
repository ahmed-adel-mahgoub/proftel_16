from odoo import models, fields, api


class CalenderEventInherit(models.Model):
    _name = 'calenderinherit'
    _inherit = ['calendar.recurrence']


