# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


def order_date_convert(value):
    return tool.parse_date(value)


##
# <Order>
#   <Customer></Customer>
#   <ShippingAddress></ShippingAddress>
#   <InvoiceAddress></InvoiceAddress>
#   <OrderLine></OrderLine>
# </Order>
# #
class OrderSheetImportMapper(models.AbstractModel):
    _name = "mapper.order.sheet.import.eat"
    _inherit = "mapper.import.eat"
    _description = "Order Mapper"

    def map_object(self, env, source, process_config):
        # Order
        order = self._build_order(env, source)
        # Customer
        customer = self._build_contact(env, source)
        # Shipping
        shipping_address = self._build_address(env, 'Shipping', source)
        # invoice
        invoice_address = self._build_address(env, 'Invoice', source)
        # order line
        order_line = self._build_order_line(env, source)
        order['customer'] = customer
        order['shipping_address'] = shipping_address
        order['invoice_address'] = invoice_address
        order['order_lines'] = [order_line]
        order['instance_id'] = env.context.get('instance_id')
        return order

    def adjust_object(self, env, order, process_config):
        return self.adjust_order(env, order)

    def adjust_map_result(self, env, result, process_config):
        return tool.adjust_data(env, result, self.adjust_order, 'client_order_ref', 'order_lines')

    def adjust_order(self, env, order):
        self.adjust_address(env, order)
        self.adjust_order_lines(env, order)
        return order

    def adjust_order_lines(self, env, order):
        order_line_items = []
        order_lines = order.pop('order_lines')
        tax = 0.0
        coupon = 0.0
        instance_id = env.context.get('instance_id')
        instance = env['connector.instance.eat'].search([('id', '=', instance_id)])
        for order_line in order_lines:
            product = order_line.pop('product', False)
            tax_line = order_line.pop('tax', False)
            coupon_line = order_line.pop('coupon', False)
            if not product:
                raise ValueError('Order {} order line product is required'.format(
                    order.get('client_order_ref', '')))
            product_line = env['product.product'].search(['|', ('default_code', '=', product), ('barcode', '=', product)])
            if not product_line:
                raise ValueError('Order {} order line product {} is not matching in system'.format(
                    order.get('client_order_ref', ''), product))
            if tax_line:
                tax = tax + tool.float_convert(tax_line)
            if coupon_line:
                coupon = coupon + tool.float_convert(coupon_line)
            order_line['product_id'] = product_line.id
            order_line_items.append((0, 0, order_line))
        if tax > 0:
            order_line_items.append((0, 0, {
                'product_id': instance.tax_product.id,
                'product_uom_qty': 1,
                'price_unit': tax
            }))
        if coupon > 0:
            order_line_items.append((0, 0, {
                'product_id': instance.coupon_product.id,
                'product_uom_qty': 1,
                'price_unit': -coupon
            }))
        order['order_line'] = order_line_items

    def adjust_address(self, env, order):
        customer = order.pop('customer')
        if customer['name']:
            order['partner'] = customer
        shipping_address = order.pop('shipping_address')
        if shipping_address['name']:
            order['shipping_address'] = shipping_address
        invoice_address = order.pop('invoice_address')
        if invoice_address['name']:
            order['invoice_address'] = invoice_address
        # shipping address is required
        if not order.get('shipping_address', False):
            raise ValueError('Order {} shipping address is required'.format(order.get('client_order_ref', '')))
        if not order.get('partner'):
            order['partner'] = tool.object_map_object([('name', 'name'), ('phone', 'phone'), ('email', 'email')],
                                                          shipping_address)

    def _build_order(self, env, source):
        return tool.object_map_object([
            ('Client Order Reference', 'client_order_ref'), ('Client Order Id', 'client_order_id'),
            ('Order Date', 'date_order', order_date_convert)], source)

    def _build_order_line(self, env, source):
        return tool.object_map_object(
            [('Order Line/Product', 'product'), ('Order Line/Unit Price', 'price_unit'),
             ('Order Line/Quantity', 'product_uom_qty'), ('Order Line/Client Order Line Id', 'client_order_line_id'),
             ('Order Line/Tax', 'tax'), ('Order Line/Coupon', 'coupon')], source)

    def _build_contact(self, env, source):
        return tool.object_map_object([
            ('Customer/Name', 'name'), ('Customer/Phone', 'phone'), ('Customer/Email', 'email')], source)

    def _build_address(self, env, address_type, source):
        address = tool.object_map_object([
            (address_type + '/Name', 'name'), (address_type + '/Address', 'street'),
            (address_type + '/Address2', 'street2'), (address_type + '/City', 'city'),
            (address_type + '/State', 'state'), (address_type + '/Zip', 'zip'),
            (address_type + '/Phone', 'phone'), (address_type + '/Email', 'email'),
            (address_type + '/Country', 'country')], source)
        country = address.pop('country')
        state = address.pop('state')
        if country:
            existing_country = env['res.country'].search(['|', ('name', '=', country), ('code', '=', country)])
            if not existing_country:
                existing_country = env['res.country'].create({'name': country})
            address['country_id'] = existing_country.id
        if state:
            country_id = address['country_id']
            existing_state = env['res.country.state'].search([('name', '=', state), ('country_id.id', '=', country_id)])
            if not existing_state:
                existing_state = env['res.country.state'].create({'name': state, 'country_id': country_id})
            address['state_id'] = existing_state.id
        return address
