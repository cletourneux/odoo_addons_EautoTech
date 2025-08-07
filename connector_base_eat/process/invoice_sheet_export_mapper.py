# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class InvoiceSheetExportMapper(models.AbstractModel):
    _name = "mapper.invoice.sheet.export.eat"
    _inherit = "mapper.eat"
    _description = "Invoice Sheet Export Mapper"

    def map(self, env, source, process_config):
        result = []
        mapping_items = [
            ('invoice_id', 'Invoice Id'),
            ('client_order_id', 'Client Order Id'),
            ('invoice_date', 'Invoice Date', tool.format_date),
            ('amount', 'Amount'),
        ]
        mapping_line_items = [
            ('product', 'Invoice Line/Product'),
            ('quantity', 'Invoice Line/Quantity'),
            ('unit_price', 'Invoice Line/Unit Price'),
        ]
        for invoice in source:
            for invoice_line in invoice['invoice_lines']:
                target_invoice = tool.object_map_object(mapping_items, invoice)
                result.append(tool.object_map_object_default(mapping_line_items, invoice_line, target_invoice))
        return result
