# models/account_move_line.py
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    price_before_discount = fields.Float(
        related='product_id.lst_price',string="orginal price"
    )

    discount_amount = fields.Float()

    @api.depends('price_unit', 'discount')
    def _compute_price_before_discount(self):
        for line in self:
            if line.discount:
                line.price_before_discount = line.price_unit / (1 - line.discount / 100.0)
            else:
                line.price_before_discount = line.price_unit
    #
    # @api.depends('price_before_discount', 'price_unit')
    # def _compute_discount_amount(self):
    #     for line in self:
    #         line.discount_amount = line.price_before_discount - line.price_unit