# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class OrderExportProcess(models.AbstractModel):
    _name = "process.order.export.eat"
    _inherit = "process.export.eat"
    _description = "Order Export process"

    def build_data_list(self, env, process_config, now):
        domains = self.build_domain(env, process_config, now)
        domains.append(('instance_id.id', '=', process_config.instance_id.id))
        sale_orders = env['sale.order'].search(domains)
        result = []
        for sale_order in sale_orders:
            order = self._build_order(env, sale_order)
            order['attributes'] = self.adjust_order_attribute(env, process_config, sale_order, order)
            # if we are the host, we export the order to 3rd system
            if not order.get('client_order_ref', False):
                order['client_order_ref'] = sale_order.name
            if not order.get('client_order_id', False):
                order['client_order_id'] = sale_order.id
            order['customer'] = self._build_contact(env, sale_order)
            order['shipping_address'] = self._build_address(env, sale_order, 'shipping')
            order['invoice_address'] = self._build_address(env, sale_order, 'invoice')
            order['order_lines'] = self._build_order_line(env, process_config, sale_order)
            result.append(order)
        return result

    def adjust_order_attribute(self, env, process_config, sale_order, target_order):
        return {}

    def _build_order(self, env, sale_order):
        return tool.object_map_object(
            [('client_order_ref', 'client_order_ref'), ('client_order_id', 'client_order_id'),
             ('create_date', 'date_order'), ('id', 'db_id')], sale_order)

    def _build_contact(self, env, sale_order):
        partner_id = sale_order.partner_id
        return tool.object_map_object([('name', 'name'), ('phone', 'phone'), ('email', 'email')], partner_id)

    def _build_address(self, env, sale_order, addr_type):
        if addr_type == 'shipping':
            address_id = sale_order.partner_shipping_id
        else:
            address_id = sale_order.partner_invoice_id
        address = tool.object_map_object([
            ('name', 'name'), ('street', 'street'), ('street2', 'street2'), ('city', 'city'), ('zip', 'zip'),
            ('phone', 'phone'), ('email', 'email')], address_id)
        if address_id.country_id:
            address['country'] = address_id.country_id.name
        if address_id.state_id:
            address['state'] = address_id.state_id.name
        return address

    def _build_order_line(self, env, process_config, sale_order):
        line_items = []
        order_lines = sale_order.order_line
        for order_line in order_lines:
            product_id = order_line.product_id
            if not product_id:
                continue
            # TODO config the tax and coupon product
            line_item = tool.object_map_object([('price_unit', 'price_unit'), ('product_uom_qty', 'product_uom_qty'),
                                                ('id', 'client_order_line_id'), ('id', 'db_id')], order_line)
            line_item['product'] = product_id.default_code
            line_item['attributes'] = self.adjust_order_line_attribute(env, process_config, sale_order, order_line)
            line_items.append(line_item)
        return line_items

    def adjust_order_line_attribute(self, env, process_config, sale_order, target_order_line):
        return {}
