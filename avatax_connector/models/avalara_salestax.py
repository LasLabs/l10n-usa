# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# Copyright 2016 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class AvalaraSalestax(models.Model):
    _name = 'avalara.salestax'
    _description = 'AvaTax Configuration'
    _sql_constraints = [
        ('code_company_uniq', 'unique (company_code)',
         'Avalara setting is already available for this company code'),
        ('account_number_company_uniq', 'unique (account_number, company_id)',
         'The account number must be unique per company!'),
    ]
    __rec_name = 'account_number'

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('avalara.salestax')

    @api.model
    def _default_country_ids(self):
        """Returns countries supported by AvaTax Address Validation Service"""
        return self.env['res.country'].search([('code', 'in', ['US', 'CA'])])

    account_number = fields.Char(
        required=True,
        help="Account Number provided by AvaTax")
    license_key = fields.Char(
        required=True,
        help="License Key provided by AvaTax",
    )
    service_url = fields.Char(
        'Service URL', required=True, help="The url to connect with")
    date_expiration = fields.Date(
        'Service Expiration Date',
        readonly=True,
        help="The expiration date of the service")
    request_timeout = fields.Integer(
        default=300,
        help='Defines AvaTax request time out length, AvaTax best practices'
             ' prescribes default setting of 300 seconds',
    )
    company_code = fields.Char(
        required=True,
        help="The company code as defined in the Admin Console of AvaTax")
    logging = fields.Boolean(
        'Enable Logging',
        help="Enables detailed AvaTax transaction logging within application")
    address_validation = fields.Boolean(
        'Disable Address Validation',
        help="Check to disable address validation")
    enable_address_validation = fields.Boolean(
        help="Check to Enable address validation",
    )
    result_in_uppercase = fields.Boolean(
        'Return validation results in upper case',
        help="Check is address validation results desired to be in upper case")
    validation_on_save = fields.Boolean(
        'Address Validation on save for customer profile',
        help='Validates the address and automatically saves when Customer'
             ' profile is saved.',
    )
    force_address_validation = fields.Boolean(
        help='Check if address validation should happen before tax calculation'
    )
    auto_generate_customer_code = fields.Boolean(
        'Automatically generate customer code',
        default=True,
        help='This will generate customer code for customers in the system who'
             ' do not have codes already created.  Each code is unique per'
             ' customer. When this is disabled, you will have to manually go'
             ' to each customer and manually generate their customer code.'
             ' This is required for Avatax and is only generated one time.',
    )
    disable_tax_calculation = fields.Boolean(
        'Disable Avalara Tax Calculation and reporting',
        default=False,
        help="Check to disable avalara tax calculation and reporting")
    disable_tax_reporting = fields.Boolean(
        'Disable Avalara Tax reporting only',
        help='Check to disable avalara tax reporting to Avatax Service. You'
             ' will not see the transactions on the Avalara web portal.',
    )
    default_shipping_code_id = fields.Many2one(
        'product.tax.code',
        'Default Shipping Code',
        help="The default shipping code which will be passed to Avalara")
    country_ids = fields.Many2many(
        'res.country',
        'avalara_salestax_country_rel',
        'avalara_salestax_id',
        'country_id',
        'Countries',
        default=lambda s: s._default_country_ids(),
        help="Countries where address validation will be used")
    active = fields.Boolean(
        default=True,
        help="Uncheck the active field to hide the record",
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda s: s._default_company_id(),
        help="Company which has subscribed to the AvaTax service")
    on_line = fields.Boolean(
        'Line-level', help="It will calculate tax line by line and also show.")
    on_order = fields.Boolean(
        'Order-level',
        default=True,
        help="It will calculate tax for order not line by line.")
    upc_enable = fields.Boolean(
        'Enable UPC Taxability',
        help="Allows ean13 to replace Item Reference as upc identifier.",
    )

    @api.onchange('on_line')
    def _onchange_on_line(self):
        if self.on_line:
            self.on_order = False
            self.on_line = self.on_line

    @api.onchange('on_order')
    def _onchange_on_order(self):
        if self.on_order:
            self.on_order = self.on_order
            self.on_line = False

    @api.model
    def _get_avatax_config_company(self):
        """ Returns the AvaTax configuration for the user company """
        return self.search([('company_id', '=', self.env.user.company_id.id)])
