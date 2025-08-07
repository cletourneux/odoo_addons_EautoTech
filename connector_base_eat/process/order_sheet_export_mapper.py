# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class OrderSheetExportMapper(models.AbstractModel):
    _name = "mapper.order.sheet.export.eat"
    _inherit = "mapper.eat"
    _description = "Order Sheet Export Mapper"

    def map(self, env, source, process_config):
        result = []
        order_mapping_items = [('client_order_ref', 'Client Order Reference'),
                               ('client_order_id', 'Client Order Id'), ('date_order', 'Order Date', tool.format_date)]
        cus_mapping_items = [('name', 'Customer/Name'), ('phone', 'Customer/Phone'), ('email', 'Customer/Email')]
        shipping_mapping_items = self._address_maping_item('Shipping')
        invoice_mapping_items = self._address_maping_item('Invoice')
        line_mapping_items = [('product', 'Order Line/Product'), ('price_unit', 'Order Line/Unit Price'),
                              ('product_uom_qty', 'Order Line/Quantity'), ('coupon', 'Order Line/Coupon'),
                              ('client_order_line_id', 'Order Line/Client Order Line Id'), ('tax', 'Order Line/Tax')]
        for order in source:
            order_lines = order['order_lines']
            for order_line in order_lines:
                line = tool.object_map_object(order_mapping_items, order)
                tool.object_map_object_default(cus_mapping_items, order['customer'], line)
                tool.object_map_object_default(shipping_mapping_items, order['shipping_address'], line)
                tool.object_map_object_default(invoice_mapping_items, order['invoice_address'], line)
                tool.object_map_object_default(line_mapping_items, order_line, line)
                result.append(line)
        return result


    def _address_maping_item(self, addr_type):
        return [
            ('name', addr_type + '/Name'), ('street', addr_type + '/Address'),
            ('street2', addr_type + '/Address2'), ('city', addr_type + '/City'),
            ('state', addr_type + '/State'), ('zip', addr_type + '/Zip'),
            ('phone', addr_type + '/Phone'), ('email', addr_type + '/Email'), ('country', addr_type + '/Country')]
