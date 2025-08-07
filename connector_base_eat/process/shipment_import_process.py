# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ShipmentImportProcess(models.AbstractModel):
    _name = "process.shipment.import.eat"
    _inherit = "process.import.eat"
    _description = "Shipment Import process"

    # TODO we could think the shipment done, but there is not stock move, we can config the stock tracking in Odoo
    #  or 3rd system (force shipment)
    # TODO add the import log with failure document
    # TODO need think the shipment integration(odoo is different from business, odoo can get the tracking number, but
    #  if we have the shipment integration, means we need send the shipment(or picking) request to 3rd system)
    def do_save_record(self, env, process_config, data):
        instance_id = process_config.instance_id
        order = env['sale.order'].search([('instance_id.id', '=', instance_id.id), '|', '|',
        ('client_order_id', '=', data['client_order_id']), ('client_order_ref', '=', data['client_order_id']),
                                          ('name', '=', data['client_order_id'])])
        if not order:
            return False
        picking_ids = order.picking_ids
        issued_pickings = picking_ids.filtered(lambda p: p.client_picking_id == data.get('shipment_id', False))
        if issued_pickings:
            _logger.info('Shipment {} for order {} did the shipment before, skipped.'.format(data['shipment_id'], order.name))
            return False
        available_pickings = picking_ids.filtered(lambda p: p.state not in ('done', 'cancel'))
        if available_pickings:
            no_inventory_tracking = data.get('no_inventory_tracking', False)
            if no_inventory_tracking:
                self._do_picking_done_no_transfer(available_pickings[0], data)
            else:
                # TODO add savepoint for the shipping item
                available_pickings.action_assign()
                entire_shipment = data.get('entire_shipment', False)
                if entire_shipment == '1':
                    self._do_full_shipment(env, data, order, available_pickings)
                else:
                    self._do_partial_shipment(env, data, order, available_pickings)
        else:
            _logger.info('No available shipment before, skipped.'.format(data['shipment_id'], order.name))
        return False

    def _do_full_shipment(self, env, data, order, available_pickings):
        for picking_id in available_pickings:
            if picking_id.show_check_availability:
                _logger.info('Not support entire shipment, please make sure enough stock')
                return False
            if picking_id.show_validate:
                picking_id['carrier_tracking_ref'] = data['tracking_number']
                ok = self._do_picking_validate(picking_id, False)
                if not ok:
                    return False
            else:
                return False
        return True

    def _do_partial_shipment(self, env, data, order, available_pickings):
        # validate the reserved qty
        available_picking = available_pickings[0]
        available_picking['carrier_tracking_ref'] = data['tracking_number']
        ship_lines = data['ship_line']
        for ship_line in ship_lines:
            ok = self._validate_avaliable_product_reserved(ship_line['product_id'], ship_line['quantity'], available_picking)
            if not ok:
                return False
        for ship_line in ship_lines:
            self._set_product_done(ship_line['product_id'], ship_line['quantity'], available_picking)
        self._do_picking_validate(available_picking, order)
        return True

    def _do_picking_validate(self, picking, order):
        backorder_wiz = picking.button_validate()
        if backorder_wiz:
            if backorder_wiz is True:
                return False
            elif backorder_wiz['res_model'] == 'stock.backorder.confirmation':
                context = backorder_wiz['context']
                biz = self.env['stock.backorder.confirmation'].with_context(**context).create({
                    'show_transfers': context.get('default_show_transfers', False),
                    'pick_ids': context.get('default_pick_ids', []),
                    'backorder_confirmation_line_ids': [
                        (0, 0, {'to_backorder': True, 'picking_id': pick_id})
                        for h, pick_id in context.get('default_pick_ids', [])
                    ]
                })
                biz.process()
                return False
        return False

    def _do_picking_done_no_transfer(self, picking, data):
        picking['carrier_tracking_ref'] = data['tracking_number']
        # if we have the ready, we just close automatically
        if picking.state != 'assigned':
            picking.action_assign()
        self._do_picking_validate(picking, False)
        return True

    def _validate_avaliable_product_reserved(self, product_id, ship_qty, picking_id):
        for picking_item in picking_id.move_line_ids:
            if picking_item.product_id.id == product_id and picking_item.product_uom_qty >= int(ship_qty):
                return True
        return False

    def _set_product_done(self, product_id, ship_qty, picking_id):
        for picking_item in picking_id.move_line_ids:
            if picking_item.product_id.id == product_id:
                picking_item['quantity'] = ship_qty
                break
