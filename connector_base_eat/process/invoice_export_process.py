# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class InvoiceExportProcess(models.AbstractModel):
    _name = "process.invoice.export.eat"
    _inherit = "process.export.eat"
    _description = "Invoice Export process"

    def build_data_list(self, env, process_config, now):
        domains = self.build_domain(env, process_config, now)
        domains.append(('instance_id.id', '=', process_config.instance_id.id))
        domains.append(('invoice_status', '=', 'invoiced'))
        orders = env['sale.order'].search(domains)
        result = []
        # item, fee, discount, tax
        for order in orders:
            invoice_lines = []
            for order_line in order.order_line:
                if order_line.product_id:
                    invoice_line = {
                        'type': self._identify_product_type(process_config, order_line.product_id),
                        'product': order_line.product_id.default_code,
                        'quantity': order_line.qty_invoiced,
                        'unit_price': order_line.price_unit
                    }
                    self.adjust_invoice_line(order, order_line, invoice_line)
                    invoice_lines.append(invoice_line)
            invoice_item = {
                'db_id': order.id,
                'invoice_id': order.id,
                'client_order_id': order.client_order_ref,
                'invoice_date': order.write_date,
                'amount': order.amount_total,
                'invoice_lines': invoice_lines
            }
            self.adjust_invoice(order, invoice_item)
            result.append(invoice_item)
        return result

    def adjust_invoice(self, order, invoice_item):
        pass

    def adjust_invoice_line(self, order, order_line, invoice_line):
        pass

    def _identify_product_type(self, process_config, product_id):
        fee = process_config.instance_id.fee_product
        tax = process_config.instance_id.tax_product
        coupon = process_config.instance_id.coupon_product
        if product_id.id == fee.id:
            return 'fee'
        elif product_id.id == tax.id:
            return 'tax'
        elif product_id.id == coupon.id:
            return 'coupon'
        return 'item'
