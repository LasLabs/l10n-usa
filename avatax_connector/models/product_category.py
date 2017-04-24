# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# Copyright 2016 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    tax_code_id = fields.Many2one(
        'product.tax.code', 'Tax Code', help="AvaTax Tax Code")
