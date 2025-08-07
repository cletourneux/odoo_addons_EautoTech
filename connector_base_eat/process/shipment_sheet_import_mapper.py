# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


def date_convert(value):
    return tool.parse_date(value)


##
# <Shipment>
#   <Order></Order>
#   <ShippingDate></ShippingDate>
#   <Tracking></Tracking>
#   <AllInOne></AllInOne>
#   <FakeShipment></FakeShipment>
#   <ShippingLines>
#       <ShippingLine>
#           <Product><Product>
#           <Quantity></Quantity>
#       </ShippingLine>
#   </ShippingLines>
# </Shipment>
# #
class ShipmentSheetImportMapper(models.AbstractModel):
    _name = "mapper.shipment.sheet.import.eat"
    _inherit = "mapper.import.eat"
    _description = "shipment Mapper"

    def map_object(self, env, source, process_config):
        shipment = self._build_shipment(env, source)
        # shipment line
        shipment_lines = self._build_shipment_line(env, source)
        shipment['shipment_lines'] = [shipment_lines]
        return shipment

    def adjust_object(self, env, shipment, process_config):
        return self.adjust_shipment(env, shipment)

    def adjust_map_result(self, env, result, process_config):
        return tool.adjust_data(env, result, self.adjust_shipment, 'shipment_id', 'shipment_lines')

    def adjust_shipment(self, env, shipment):
        self.adjust_shipment_lines(env, shipment)
        return shipment

    def adjust_shipment_lines(self, env, shipment):
        shipment_line_items = []
        if shipment['entire_shipment'] == '1':
            shipment['ship_line'] = shipment_line_items
            return
        shipment_lines = shipment.pop('shipment_lines')
        for shipment_line in shipment_lines:
            product = shipment_line.pop('product', False)
            if not product:
                raise ValueError('Order {} shipment line product is required'.format(
                    shipment.get('client_order_id', '')))
            product_line = env['product.product'].search(['|', ('default_code', '=', product), ('barcode', '=', product)])
            if not product_line:
                raise ValueError('Order {} shipment line product {} is not matching in system'.format(
                    shipment.get('client_order_id', ''), product))
            shipment_line['product_id'] = product_line.id
            shipment_line_items.append(shipment_line)
        shipment['ship_line'] = shipment_line_items

    def _build_shipment(self, env, source):
        return tool.object_map_object(
            [('Shipment Id', 'shipment_id'), ('Client Order Id', 'client_order_id'),
             ('Shipping Date', 'shipping_date', date_convert), ('Carrier', 'carrier'),  ('Method', 'method'),
             ('Tracking Number', 'tracking_number'), ('Entire Shipment', 'entire_shipment')], source)

    def _build_shipment_line(self, env, source):
        return tool.object_map_object([('Shipping Line/Product', 'product'),
                                            ('Shipping Line/Quantity', 'quantity')], source)
