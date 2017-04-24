from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    tax_amt = fields.Float('Avalara Tax', help="tax calculate by avalara")
