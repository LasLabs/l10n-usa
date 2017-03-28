# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# Copyright 2016 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Avalara Avatax Connector",
    "version": "10.0.1.0.0",
    "author": "Odoo S.A., "
              "LasLabs, "
              "Odoo Community Association (OCA)",
    "summary": "US Sales Tax Calculation",
    "category": "Accounting",
    "website": "https://odoo-community.org",
    "depends": [
        'account_accountant',
        'sale',
    ],
    "data": [
        "security/avalara_salestax_security.xml",
        "security/ir.model.access.csv",
        "wizard/avalara_salestax_ping_view.xml",
        "wizard/avalara_salestax_address_validate_view.xml",
        "views/avalara_salestax_view.xml",
        "views/avalara_salestax_data.xml",
        "views/partner_view.xml",
        "views/product_view.xml",
        "views/account_invoice_workflow.xml",
        "views/account_invoice_view.xml",
        "views/sale_order_view.xml",
        "views/account_tax_view.xml",
    ],
    'demo': [
        "views/demo.xml",
    ],
    'images': [
        'static/description/avatax.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
