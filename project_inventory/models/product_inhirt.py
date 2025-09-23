# models/product.py
from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    project_ids = fields.Many2many(
        'project.project',
        'project_product_rel',
        'product_id',
        'project_id',
        string='Projects',
        help='Projects associated with this product'
    )