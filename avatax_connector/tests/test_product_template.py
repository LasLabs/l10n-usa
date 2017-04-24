# -*- coding: utf-8 -*-
# Copyright 2016 LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):

    def setUp(self):
        super(TestProductTemplate, self).setUp()

        self.test_code_1 = self.env.ref('avatax_connector.demo_tax_code_1')
        self.test_code_2 = self.env.ref('avatax_connector.demo_tax_code_2')

        self.test_product = self.env.ref('avatax_connector.demo_product_1')
        self.test_product.categ_id.tax_code_id = self.test_code_1
        self.test_product.prod_tax_code_id = self.test_code_2

    def test_compute_tax_code_id_override(self):
        """Should set tax code to product tax code when override is active"""
        self.test_product.override_categ_tax_code = True

        self.assertEqual(self.test_product.tax_code_id, self.test_code_2)

    def test_compute_tax_code_id_no_override(self):
        """Should set tax code to category tax code when override not active"""
        self.test_product.override_categ_tax_code = False

        self.assertEqual(self.test_product.tax_code_id, self.test_code_1)
