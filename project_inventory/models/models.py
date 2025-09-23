# models/project.py
from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    inventory_location_id = fields.Many2one(
        'stock.location',
        string='Inventory Location',
        help='Inventory location associated with this project'
    )

    inventory_count = fields.Integer(
        string='Inventory Items',
        compute='_compute_inventory_count',
        store=False
    )

    product_ids = fields.Many2many(
        'product.product',
        'project_product_rel',
        'project_id',
        'product_id',
        string='Products',
        help='Products associated with this project'
    )

    product_count = fields.Integer(
        string='Product Count',
        compute='_compute_product_count',
        store=True
    )

    @api.depends('product_ids')
    def _compute_product_count(self):
        for project in self:
            project.product_count = len(project.product_ids)

    def _compute_inventory_count(self):
        for project in self:
            if project.inventory_location_id:
                quant_obj = self.env['stock.quant']
                quants = quant_obj.search(
                    [('location_id', '=', project.inventory_location_id.id)])
                project.inventory_count = len(quants)
            else:
                project.inventory_count = 0

    def action_view_inventory(self):
        self.ensure_one()
        if not self.inventory_location_id:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'name': f'Inventory - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.inventory_location_id.id)],
            'context': {
                'default_location_id': self.inventory_location_id.id,
                'search_default_location_id': self.inventory_location_id.id
            }
        }

    def action_view_products(self):
        self.ensure_one()
        return {
            'name': f'Products - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.product_ids.ids)],
            'context': {
                'default_project_ids': [(4, self.id)],
                'search_default_filter_available': 1
            }
        }