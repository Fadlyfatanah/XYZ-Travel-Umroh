from odoo import models, fields, api\

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    manifest_line = fields.One2many('manifest.lines', 'order_id')
