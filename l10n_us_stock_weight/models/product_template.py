# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    weight_oz = fields.Float(
        compute='_compute_weight_oz',
        inverse='_inverse_weight_oz',
        help='Weight of the product, in ounces.',
    )

    @api.model_cr_context
    def _convert_kg_ounces(self, quantity, to_oz=True):
        """Convert between kg and oz.

        Args:
            quantity (float): Amount to convert.
            to_oz (bool): Set to True if ``quantity`` is in kg, otherwise
                False.

        Returns:
            float: The value of ``quantity`` in either kg or oz, depending on
                ``to_oz``.
        """
        oz = self.env.ref('product.product_uom_oz')
        kg = self.env.ref('product.product_uom_kgm')
        if to_oz:
            return kg._compute_quantity(quantity, oz)
        else:
            return oz._compute_quantity(quantity, kg)

    @api.multi
    def _compute_weight_oz(self):
        for record in self:
            record.weight_oz = self._convert_kg_ounces(record.weight)

    @api.multi
    def _inverse_weight_oz(self):
        for record in self:
            record.weight = self._convert_kg_ounces(
                record.weight, to_oz=False,
            )
