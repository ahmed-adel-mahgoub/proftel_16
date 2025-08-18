# -*- coding: utf-8 -*-

from odoo import models, fields, api


class permissions(models.Model):
    _name = 'permissions'
    _description = 'permissions'

    name = fields.Char()


