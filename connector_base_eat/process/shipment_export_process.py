# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class ShipmentExportProcess(models.AbstractModel):
    _name = "process.shipment.export.eat"
    _inherit = "process.export.eat"
    _description = "Shipment Export process"

    def build_data_list(self, env, process_config, now):
        domains = self.build_domain(env, process_config, now)
        domains.append(('sale_id.instance_id.id', '=', process_config.instance_id.id))
        domains.append(('picking_type_id.code', '=', 'outgoing'))
        domains.append(('state', '=', 'done'))
        pickings = env['stock.picking'].search(domains)
        result = []
        for picking in pickings:
            shipment_lines = []
            for picking_item in picking.move_ids_without_package:
                if picking_item.quantity_done > 0 and picking_item.sale_line_id.client_order_line_id:
                    shipment_line = {'product': picking_item.product_id.default_code, 'quantity': picking_item.quantity_done,
                                     'client_order_line_id': picking_item.sale_line_id.client_order_line_id}
                    self.adjust_shipment_line(picking.sale_id, picking_item.sale_line_id, shipment_line)
                    shipment_lines.append(shipment_line)
            picking_line = {
                'db_id': picking.id,
                'shipment_id': picking.id,
                'client_order_id': picking.sale_id.client_order_id,
                'client_order_reference': picking.sale_id.client_order_ref,
                'shipping_date': picking.date_done,
                'carrier': picking.carrier_id.delivery_type,
                'method': picking.carrier_id.name,
                'tracking_number': picking.carrier_tracking_ref,
                'entire_shipment': False,
                'shipment_lines': shipment_lines
            }
            self.adjust_shipment(picking.sale_id, picking_line)
            result.append(picking_line)
        return result

    def adjust_shipment(self, order, shipment_item):
        pass

    def adjust_shipment_line(self, order, order_line, shipment_line):
        pass
