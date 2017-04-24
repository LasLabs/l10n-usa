from odoo import fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    tax_amt = fields.Float('Avalara Tax', help='tax calculate by avalara')
