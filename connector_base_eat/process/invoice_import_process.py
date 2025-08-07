# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class InvoiceImportProcess(models.AbstractModel):
    _name = "process.invoice.import.eat"
    _inherit = "process.import.eat"
    _description = "invoice Import process"

    def do_save_record(self, env, process_config, data):
        instance_id = process_config.instance_id
        order = env['sale.order'].search(
            ['|', '|', ('client_order_ref', '=', data['client_order_id']), ('name', '=', data['client_order_id']),
             ('client_order_id', '=', data['client_order_id']), ('instance_id.id', '=', instance_id.id)])
        if not order:
            return False
        if order.invoice_status != 'to invoice':
            _logger.info('Not ready for invoice, please try later.')
            return False
        self._create_invoice(env, order)
        return False

    def _create_invoice(self, env, order):
        try:
            payment = env['sale.advance.payment.inv'].with_context({
                'active_model': 'sale.order',
                'active_ids': [order.id],
                'active_id': order.id,
            }).create({
                'advance_payment_method': 'delivered',
            })
            payment.create_invoices()
            return True
        except Exception as e:
            return False

