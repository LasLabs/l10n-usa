# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# Copyright 2016 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    'name': 'Avalara Avatax Connector',
    'version': '10.0.1.0.0',
    'author': 'Odoo S.A., '
              'LasLabs, '
              'Odoo Community Association (OCA)',
    'summary': 'US Sales Tax Calculation',
    'category': 'Accounting',
    'website': 'https://odoo-community.org',
    'depends': [
        'account_accountant',
        'sale',
        'stock',
    ],
    'data': [
        'data/account_tax.xml',
        'data/exemption_code.xml',
        'data/res_groups.xml',
        'security/avalara_salestax.xml',
        'security/ir.model.access.csv',
        'security/product_tax_code.xml',
        'views/account_invoice.xml',
        'views/account_invoice_line.xml',
        'wizards/avalara_salestax_ping.xml',
        'views/account_tax.xml',
        'views/avalara_salestax.xml',
        'views/exemption_code.xml',
        'views/product_category.xml',
        'views/product_tax_code.xml',
        'views/product_template.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'wizards/avalara_salestax_address_validate.xml',
    ],
    'demo': [
        'demo/avalara_salestax.xml',
        'demo/product_tax_code.xml',
        'demo/product_template.xml',
    ],
    'images': [
        'static/description/avatax.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
