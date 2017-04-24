from odoo import api, fields, models


class ProductTaxCode(models.Model):
    """ Define type of tax code:
    @param type: product is use as product code,
    @param type: freight is use for shipping code
    @param type: service is use for service type product
    """
    _name = 'product.tax.code'
    _description = 'Tax Code'

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('product.tax.code')

    name = fields.Char('Code', required=True)
    description = fields.Char()
    type = fields.Selection(
        [
            ('product', 'Product'),
            ('freight', 'Freight'),
            ('service', 'Service'),
            ('digital', 'Digital'),
            ('other', 'Other')
        ],
        required=True,
        help="Type of tax code as defined in AvaTax",
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda s: s._default_company_id(),
    )
