from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    tax_code_id = fields.Many2one(
        comodel_name='product.tax.code',
        compute='_compute_tax_code_id',
        string='Effective Tax Code',
        help='AvaTax tax code. By default, this is based on the tax'
             ' code of the product\'s internal category, but it can be changed'
             ' for this product by checking the override box.',
    )
    override_categ_tax_code = fields.Boolean(
        string='Override Category Tax Code?',
        help='Check this box to override the category tax code and use the'
             ' product tax code selected here',
    )
    prod_tax_code_id = fields.Many2one(
        comodel_name='product.tax.code',
        string='Product Tax Code',
        help='AvaTax tax code for this product',
    )
    tax_apply = fields.Boolean(
        string='Calculate Tax?',
        default=True,
        help='Uncheck this box to avoid AvaTax calculations for this product',
    )

    @api.multi
    @api.depends(
        'override_categ_tax_code',
        'prod_tax_code_id',
        'categ_id.tax_code_id',
    )
    def _compute_tax_code_id(self):
        for record in self:
            if record.override_categ_tax_code:
                record.tax_code_id = record.prod_tax_code_id
            else:
                record.tax_code_id = record.categ_id.tax_code_id
