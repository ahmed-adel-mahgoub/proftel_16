from odoo import fields,api,models

class lock_door(models.Model):
    _name='lock.door'
    _description = 'lock_door'

    name = fields.Char()
    rf_id = fields.Char()
    category = fields.Selection([
        ("product","Product"),("assets","Assets"),
    ])
    country = fields.Char()
    late = fields.Char()
    long = fields.Char()
    location = fields.Char()
    city = fields.Char()
    room = fields.Char()

    @api.model
    def create(self, vals):
        record = super(lock_door, self).create(vals)
        if record.category == 'product':
            record.create_inventory_record()
        return record

    def write(self, vals):
        res = super(lock_door, self).write(vals)
        if 'category' in vals and vals.get('category') == 'product':
            self.create_inventory_record()
        return res

    def create_inventory_record(self):
        Inventory = self.env['stock.quant']
        Product = self.env['product.product']
        stock_location = self.env.ref('stock.stock_location_stock')

        # Find or create a product based on the lock door information
        product = Product.search([('name', '=', self.name)], limit=1)
        if not product:
            product = Product.create({
                'name': self.name,
                'type': 'product',
                'categ_id': self.env.ref('product.product_category_all').id,
            })

        # Check if inventory record already exists for this product in this location
        existing_quant = Inventory.search([
            ('product_id', '=', product.id),
            ('location_id', '=', stock_location.id)
        ], limit=1)

        if not existing_quant:
            Inventory.create({
                'product_id': product.id,
                'location_id': stock_location.id,
                'quantity': 1,
                'inventory_quantity': 1,
            })