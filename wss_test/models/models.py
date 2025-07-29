# -*- coding: utf-8 -*-

from odoo import models, fields, api


class wss_test(models.Model):
    _name = 'wss.test'
    _description = 'wss_test'

    name = fields.Char()
    age = fields.Integer()
