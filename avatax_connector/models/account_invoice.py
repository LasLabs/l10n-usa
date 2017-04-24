# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# Copyright 2016 Odoo S.A.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import time
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    """Inherit to implement the tax calculation using Avatax API."""

    _inherit = "account.invoice"

    invoice_doc_no = fields.Char(
        string='Source/Ref Invoice No',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Reference of the invoice",
    )
    invoice_date = fields.Date(readonly=True)
    is_add_validate = fields.Boolean(
        string='Address validated',
    )
    exemption_code = fields.Char(
        string='Exemption Number',
        help="It shows the customer exemption number",
    )
    exemption_code_id = fields.Many2one(
        string='Exemption Code',
        comodel_name='exemption.code',
        help="It show the customer exemption code",
    )
    tax_add_default = fields.Boolean(
        string='Default Address',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    tax_add_invoice = fields.Boolean(
        string='Invoice Address',
        default=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    tax_add_shipping = fields.Boolean(
        string='Delivery Address',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    shipping_add_id = fields.Many2one(
        string='Tax Address',
        comodel_name='res.partner',
        change_default=True,
        track_visibility='always',
    )
    shipping_address = fields.Text(
        string='Tax Address',
    )
    location_code = fields.Char(
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id_company_id(self):
        self.exemption_code = self.partner_id.exemption_number or ''
        self.exemption_code_id = self.partner_id.exemption_code_id.id or None
        self.is_add_validate = bool(self.partner_id.validation_method)

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            if self.warehouse.company_id:
                self.company_id = self.warehouse.company_id.id
            if self.warehouse.code:
                self.location_code = self.warehouse.code

    @api.onchange('tax_add_default', 'origin', 'partner_id')
    def _onchange_tax_add_default_origin_partner_id(self):
        if self.tax_add_default:
            shipping_add_id = self.partner_id.id
            if self.origin:
                if len(self.origin.split(':')) > 1:
                    so_origin = self.origin.split(':')[1]
                else:
                    so_origin = self.origin.split(':')[0]

                sale_ids = self.env['sale.order'].search(
                    [('name', '=', so_origin)])
                if sale_ids:
                    shipping_add_id = sale_ids[0].partner_shipping_id.id
            self.tax_add_default = True
            self.tax_add_invoice = False
            self.tax_add_shipping = False
            self.shipping_add_id = shipping_add_id

    @api.onchange('tax_add_invoice', 'partner_id')
    def _onchange_tax_add_invoice_partner_id(self):
        if self.tax_add_invoice and self.partner_id:
            self.tax_add_default = False
            self.tax_add_invoice = True
            self.tax_add_shipping = False
            self.shipping_add_id = self.partner_id.id

    @api.onchange('tax_add_shipping', 'origin', 'partner_id')
    def _onchange_tax_add_shipping_origin_partner_id(self):
        if self.tax_add_shipping:
            shipping_add_id = self.partner_id.id
            if self.origin:
                if len(self.origin.split(':')) > 1:
                    so_origin = self.origin.split(':')[1]
                else:
                    so_origin = self.origin.split(':')[0]

                sale_ids = self.env['sale.order'].search(
                    [('name', '=', so_origin)])
                if sale_ids:
                    shipping_add_id = sale_ids[0].partner_shipping_id.id
            self.tax_add_default = False
            self.tax_add_invoice = False
            self.tax_add_shipping = True
            self.shipping_add_id = shipping_add_id

    @api.multi
    def write(self, vals):
        for self_obj in self:

            ship_add_id = self_obj.shipping_add_id
            if 'tax_add_invoice' in vals and vals['tax_add_invoice']:
                ship_add_id = self_obj.partner_id

            elif 'tax_add_default' in vals and vals['tax_add_default']:
                if self_obj.origin:
                    if len(self_obj.origin.split(':')) > 1:
                        so_origin = self_obj.origin.split(':')[1]
                    else:
                        so_origin = self_obj.origin.split(':')[0]

                    sale_ids = self.env['sale.order'].search([
                        ('name', '=', so_origin),
                    ])
                    if sale_ids:
                        ship_add_id = sale_ids[0].partner_id

            elif 'tax_add_shipping' in vals and vals['tax_add_shipping']:
                if self_obj.origin:
                    if len(self_obj.origin.split(':')) > 1:
                        so_origin = self_obj.origin.split(':')[1]
                    else:
                        so_origin = self_obj.origin.split(':')[0]

                    sale_ids = self.env['sale.order'].search([
                        ('name', '=', so_origin),
                    ])
                    if sale_ids:
                        ship_add_id = sale_ids[0].partner_shipping_id
            if ship_add_id:
                vals['shipping_add_id'] = ship_add_id.id
            else:
                vals['shipping_add_id'] = self_obj.partner_id.id

        return super(AccountInvoice, self).write(vals)

    @api.multi
    def action_commit_tax(self):
        avatax_config_obj = self.env['avalara.salestax']
        account_tax_obj = self.env['account.tax']

        avatax_config = avatax_config_obj._get_avatax_config_company()

        if avatax_config and avatax_config.disable_tax_reporting:
            return True

        for invoice in self:
            if avatax_config and not avatax_config.disable_tax_calculation \
                    and invoice.type in ['out_invoice', 'out_refund']:
                shipping_add_id = self.shipping_add_id
                if self.warehouse_id and self.warehouse_id.partner_id:
                    shipping_add_origin_id = self.warehouse_id.partner_id
                else:
                    shipping_add_origin_id = self.company_id.partner_id
                tax_date = self._get_origin_tax_date()
                if not tax_date:
                    tax_date = invoice.date_invoice

                sign = invoice.type == 'out_invoice' and 1 or -1
                lines = self.create_lines(invoice.invoice_line_ids, sign)
                if lines:
                    if avatax_config.on_line:
                        for line in lines:
                            ol_tax_amt = account_tax_obj._get_compute_tax(
                                avatax_config,
                                invoice.date_invoice,
                                invoice.number,
                                'SalesOrder',
                                invoice.partner_id,
                                shipping_add_origin_id,
                                shipping_add_id,
                                [line],
                                invoice.user_id,
                                invoice.exemption_code or None,
                                invoice.exemption_code_id.code or None,
                            ).TotalTax

                            line['id'].write({'tax_amt': ol_tax_amt})

                    elif avatax_config.on_order:
                        for o_line in invoice.invoice_line_ids:
                            o_line.write({'tax_amt': 0.0, })
                    else:
                        raise UserError(_(
                            'Please select system calls in Avatax API Config.'
                        ))

                else:
                    for o_line in invoice.invoice_line_ids:
                        o_line.write({'tax_amt': 0.0, })

                # extend list lines1 with lines2 to send all invoice lines in
                # avalara
                if lines:
                    account_tax_obj._get_compute_tax(
                        avatax_config,
                        invoice.date_invoice,
                        invoice.number,
                        (not invoice.invoice_doc_no and 'SalesInvoice'
                            or 'ReturnInvoice'),
                        invoice.partner_id,
                        shipping_add_origin_id,
                        shipping_add_id,
                        lines,
                        invoice.user_id,
                        invoice.exemption_code or None,
                        invoice.exemption_code_id.code or None,
                        False,
                        tax_date,
                        invoice.invoice_doc_no,
                        invoice.location_code or '',
                    )
            else:
                for o_line in invoice.invoice_line_ids:
                    o_line.write({'tax_amt': 0.0, })
        return True

    @api.multi
    def action_cancel(self):
        account_tax_obj = self.env['account.tax']
        avatax_conf = self.env['avalara.salestax']._get_avatax_config_company()
        for invoice in self:
            c_code = invoice.partner_id.country_id \
                and invoice.partner_id.country_id.code or False
            cs_code = []  # Countries where Avalara address validation enabled
            for c_brw in avatax_conf.country_ids:
                cs_code.append(str(c_brw.code))
            if avatax_conf and not avatax_conf.disable_tax_calculation \
                    and invoice.type in ['out_invoice', 'out_refund'] \
                    and c_code in cs_code:
                doc_type = (invoice.type == 'out_invoice' and 'SalesInvoice'
                            or 'ReturnInvoice')
                account_tax_obj.cancel_tax(
                    avatax_conf, invoice.number, doc_type, 'DocVoided')

        return super(AccountInvoice, self).action_cancel()

    @api.multi
    def compute(self):
        avatax_config_obj = self.env['avalara.salestax']
        account_tax_obj = self.env['account.tax']

        avatax_config = avatax_config_obj._get_avatax_config_company()

        for invoice in self:
            if avatax_config and not avatax_config.disable_tax_calculation \
                    and invoice.type in ['out_invoice', 'out_refund']:
                shipping_add_id = self.shipping_add_id
                if self.warehouse_id and self.warehouse_id.partner_id:
                    shipping_add_origin_id = self.warehouse_id.partner_id
                else:
                    shipping_add_origin_id = self.company_id.partner_id
                tax_date = self._get_origin_tax_date()
                if not tax_date:
                    tax_date = invoice.date_invoice or time.strftime(
                        '%Y-%m-%d')

                sign = invoice.type == 'out_invoice' and 1 or -1
                lines = self.create_lines(invoice.invoice_line_ids, sign)
                if lines:
                    if avatax_config.on_line:
                        ava_tax = account_tax_obj.search(
                            [('is_avatax', '=', True),
                             ('type_tax_use', 'in', ['sale', 'all']),
                             ('company_id', '=', self.company_id.id)])
                        tax_id = []
                        for line in lines:
                            tax_id = line['tax_id'] and [
                                tax.id for tax in line['tax_id']] or []
                            if ava_tax and ava_tax[0].id not in tax_id:
                                tax_id.append(ava_tax[0].id)
                            ol_tax_amt = account_tax_obj._get_compute_tax(
                                avatax_config,
                                invoice.date_invoice,
                                invoice.number,
                                'SalesOrder',
                                invoice.partner_id,
                                shipping_add_origin_id,
                                shipping_add_id,
                                [line],
                                invoice.user_id,
                                invoice.exemption_code or None,
                                invoice.exemption_code_id.code or None,
                            ).TotalTax

                            line['id'].write({
                                'tax_amt': ol_tax_amt,
                                'invoice_line_tax_ids': [(6, 0, tax_id)]
                            })

                    elif avatax_config.on_order:
                        for o_line in invoice.invoice_line_ids:
                            o_line.write({'tax_amt': 0.0, })
                else:
                    for o_line in invoice.invoice_line_ids:
                        o_line.write({'tax_amt': 0.0, })
        return True

    @api.multi
    def invoice_validate(self):
        super_result = super(AccountInvoice, self).invoice_validate()
        self.action_commit_tax()
        return super_result

    @api.multi
    def action_invoice_paid(self):
        """Overload to log newly paid invoices in AvaTax"""
        super_result = super(AccountInvoice, self).action_invoice_paid()
        avatax_config_obj = self.env['avalara.salestax']
        account_tax_obj = self.env['account.tax']
        avatax_config = avatax_config_obj._get_avatax_config_company()

        # Bypass reporting
        if avatax_config and avatax_config.disable_tax_reporting:
            return super_result

        for invoice in self:
            if avatax_config and not avatax_config.disable_tax_calculation \
                    and invoice.type in ['out_invoice', 'out_refund']:
                shipping_add_id = invoice.shipping_add_id
                if invoice.warehouse_id and invoice.warehouse_id.partner_id:
                    shipping_add_origin_id = invoice.warehouse_id.partner_id
                else:
                    shipping_add_origin_id = invoice.company_id.partner_id
                tax_date = self._get_origin_tax_date()
                if not tax_date:
                    tax_date = invoice.date_invoice

                sign = invoice.type == 'out_invoice' and 1 or -1
                lines = self.create_lines(invoice.invoice_line_ids, sign)
                if lines:
                    account_tax_obj._get_compute_tax(
                        avatax_config,
                        invoice.date_invoice,
                        invoice.number,
                        (not invoice.invoice_doc_no and 'SalesInvoice'
                            or 'ReturnInvoice'),
                        invoice.partner_id,
                        shipping_add_origin_id,
                        shipping_add_id,
                        lines,
                        invoice.user_id,
                        invoice.exemption_code or None,
                        invoice.exemption_code_id.code or None,
                        True,
                        tax_date,
                        invoice.invoice_doc_no,
                        invoice.location_code or '',
                    )

        return super_result

    @api.multi
    def get_taxes_values(self):
        avatax_conf = self.env['avalara.salestax']._get_avatax_config_company()
        account_tax_obj = self.env['account.tax']
        tax_grouped = {}
        if avatax_conf and not avatax_conf.disable_tax_calculation \
                and self.type in ['out_invoice', 'out_refund']:

            if self.invoice_line_ids:
                lines = self.create_lines(self.invoice_line_ids)
                if lines:
                    if self.warehouse_id and self.warehouse_id.partner_id:
                        ship_from_address_id = self.warehouse_id.partner_id
                    else:
                        ship_from_address_id = self.company_id.partner_id

                    shipping_add_id = self.shipping_add_id
                    o_tax_amt = 0.0
                    tax = account_tax_obj.search(
                        [('is_avatax', '=', True),
                         ('type_tax_use', 'in', ['sale', 'all']),
                         ('company_id', '=', self.company_id.id)])
                    if not tax:
                        raise UserError(_(
                            'Please configure tax information in "AVATAX"'
                            ' settings. The documentation will assist you in'
                            ' configuring all the tax code settings as well as'
                            ' how they relate to the product.'
                            ' \n\n Accounting->Configuration->Taxes->Taxes'
                        ))

                    o_tax_amt = account_tax_obj._get_compute_tax(
                        avatax_conf,
                        self.date_invoice or time.strftime('%Y-%m-%d'),
                        self.number,
                        (self.type == 'out_invoice' and 'SalesOrder'
                            or 'ReturnOrder'),
                        self.partner_id,
                        ship_from_address_id,
                        shipping_add_id,
                        lines,
                        self.user_id,
                        self.exemption_code or None,
                        self.exemption_code_id.code or None,
                    ).TotalTax
                    if o_tax_amt:

                        val = {
                            'invoice_id': self.id,
                            'name': tax[0].name,
                            'tax_id': tax[0].id,
                            'amount': o_tax_amt,
                            'manual': False,
                            'sequence': tax[0].sequence,
                            'account_analytic_id': tax[0].analytic
                            and lines[0]['account_analytic_id'] or False,
                            'account_id':
                            self.type in ('out_invoice', 'in_invoice')
                            and (tax[0].account_id.id
                                 or lines[0]['account_id'])
                            or (tax[0].refund_account_id.id
                                or lines[0]['account_id']),
                        }
                        if not val.get('account_analytic_id') and \
                                lines[0]['account_analytic_id'] and \
                                val['account_id'] == lines[0]['account_id']:
                            val['account_analytic_id'] \
                                = lines[0]['account_analytic_id']

                        key = tax[0].id
                        if key not in tax_grouped:
                            tax_grouped[key] = val
                        else:
                            tax_grouped[key]['amount'] += val['amount']

                for line in self.invoice_line_ids:
                    price_unit = line.price_unit * \
                        (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.invoice_line_tax_ids.compute_all(
                        price_unit,
                        self.currency_id,
                        line.quantity,
                        line.product_id,
                        self.partner_id)['taxes']
                    for tax in taxes:
                        val = {
                            'invoice_id': self.id,
                            'name': tax['name'],
                            'tax_id': tax['id'],
                            'amount': tax['amount'],
                            'manual': False,
                            'sequence': tax['sequence'],
                            'account_analytic_id': tax['analytic']
                            and line.account_analytic_id.id or False,
                            'account_id':
                            self.type in ('out_invoice', 'in_invoice')
                            and (tax['account_id'] or line.account_id.id)
                            or (tax['refund_account_id']
                                or line.account_id.id),
                        }

                        # If the taxes generate moves on the same financial
                        # account as the invoice line, propagate the analytic
                        # account from the invoice line to the tax line. This
                        # is necessary in situations were (part of) the taxes
                        # cannot be reclaimed, to ensure the tax move is
                        # allocated to the proper analytic account.
                        if not val.get('account_analytic_id') \
                                and line.account_analytic_id \
                                and val['account_id'] == line.account_id.id:
                            val['account_analytic_id'] \
                                = line.account_analytic_id.id

                        key = tax['id']
                        if key not in tax_grouped:
                            tax_grouped[key] = val
                        else:
                            tax_grouped[key]['amount'] += val['amount']
                return tax_grouped

        else:
            tax_grouped = super(AccountInvoice, self).get_taxes_values()
        return tax_grouped

    @api.model
    def create_lines(self, invoice_lines, sign=1):

        avatax_config_obj = self.env['avalara.salestax']
        avatax_config = avatax_config_obj._get_avatax_config_company()
        lines = []
        for line in invoice_lines:

            # Add UPC to product item code
            if line.product_id.barcode and avatax_config.upc_enable:
                item_code = "upc:" + line.product_id.barcode
            else:
                item_code = line.product_id.default_code

            # Get Tax Code
            if line.product_id and line.product_id.tax_apply:
                tax_code = line.product_id.tax_code_id \
                    and line.product_id.tax_code_id.name or None

                # Calculate discount amount
                discount_amount = 0.0
                is_discounted = False
                if line.discount != 0.0 or line.discount is not None:
                    discount_amount = sign * line.price_unit * \
                        ((line.discount or 0.0) / 100.0) * line.quantity,
                    is_discounted = True
                lines.append({
                    'qty': line.quantity,
                    'itemcode': line.product_id and item_code or None,
                    'description': line.name,
                    'discounted': is_discounted,
                    'discount': discount_amount[0],
                    'amount': sign * line.price_unit * line.quantity *
                            (1 - (line.discount or 0.0) / 100.0),
                    'tax_code': tax_code,
                    'id': line,
                    'account_analytic_id': line.account_analytic_id.id,
                    'account_id': line.account_id.id,
                    'tax_id': line.invoice_line_tax_ids,
                })
        return lines

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None,
                        date=None, description=None, journal_id=None):
        values = super(AccountInvoice, self)._prepare_refund(
            invoice,
            date_invoice=date_invoice,
            date=date,
            description=description,
            journal_id=journal_id,
        )
        values.update({
            'invoice_doc_no': invoice.number,
            'invoice_date': invoice.date_invoice,
            'tax_add_default': invoice.tax_add_default,
            'tax_add_invoice': invoice.tax_add_invoice,
            'tax_add_shipping': invoice.tax_add_shipping,
            'warehouse_id': invoice.warehouse_id.id,
            'location_code': invoice.location_code,
            'exemption_code': invoice.exemption_code or '',
            'exemption_code_id': invoice.exemption_code_id.id or None,
            'shipping_add_id': invoice.shipping_add_id.id,

        })
        return values

    @api.multi
    def _get_origin_tax_date(self):
        """Partner address, on which Avalara tax will calculate."""
        self.ensure_one()
        if self.origin:
            a = self.origin

            if len(a.split(':')) > 1:
                inv_origin = a.split(':')[1]
            else:
                inv_origin = a.split(':')[0]

            origin = self.search([
                ('number', '=', inv_origin),
            ],
                limit=1,
            )
            return origin.date_invoice or self.date_invoice
        else:
            return False
