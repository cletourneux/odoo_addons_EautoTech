# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ShipmentSheetExportMapper(models.AbstractModel):
    _name = "mapper.shipment.sheet.export.eat"
    _inherit = "mapper.eat"
    _description = "Shipment Sheet Export Mapper"

    def map(self, env, source, process_config):
        result = []
        mapping_items = [
            ('shipment_id', 'Shipment Id'), ('client_order_id', 'Client Order Id'),
            ('shipping_date', 'Shipping Date', tool.format_date), ('carrier', 'Carrier'),
            ('method', 'Method'), ('tracking_number', 'Tracking Number'),
            ('entire_shipment', 'Entire Shipment'),
        ]
        mapping_line_items = [
            ('product', 'Shipment Line/Product'),
            ('quantity', 'Shipment Line/Quantity'),
        ]
        for shipment in source:
            for shipment_line in shipment['shipment_lines']:
                target_shipment = tool.object_map_object(mapping_items, shipment)
                result.append(tool.object_map_object_default(mapping_line_items, shipment_line, target_shipment))
        return result
