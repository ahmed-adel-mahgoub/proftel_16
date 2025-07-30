# models/account_move_line.py
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    original_price_unit = fields.Float(
        string='Unit Price (Before Discount)',
        digits='Product Price',
        default=lambda self: self._default_original_price_unit(),
        help="Stores the original price before any discounts"
    )

    discount_amount = fields.Float(
        string='Discount Amount',
        compute='_compute_discount_amount',
        store=True,
        digits='Product Price'
    )

    def _default_original_price_unit(self):
        """Set default original price to match price_unit"""
        return self.price_unit

    @api.depends('original_price_unit', 'price_unit')
    def _compute_discount_amount(self):
        for line in self:
            line.discount_amount = line.original_price_unit - line.price_unit

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'original_price_unit' not in vals:
                vals['original_price_unit'] = vals.get('price_unit', 0.0)
        return super().create(vals_list)

    def write(self, vals):
        if 'price_unit' in vals and 'original_price_unit' not in vals:
            for line in self:
                if not line.original_price_unit:
                    vals['original_price_unit'] = vals['price_unit']
        return super().write(vals)