# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class InventoryImportProcess(models.AbstractModel):
    _name = "process.inventory.import.eat"
    _inherit = "process.import.eat"
    _description = "Inventory Import process"

    def do_save(self, env, process_config, data_list):
        warehouse = process_config.instance_id.warehouse_id
        stock_id = warehouse.lot_stock_id
        product_ids = []
        for data in data_list:
            product_reference = data['product_reference']
            product_id = env['product.product'].search([('default_code', '=', product_reference)], limit=1)
            if product_id:
                data['product_id'] = product_id
                product_ids.append(product_id.id)
            else:
                data['product_id'] = False
        inventory = self._create_stock_inventory(env, product_ids, data_list, stock_id)
        if inventory:
            inventory.action_validate()
        return False

    def _create_stock_inventory(self, env, product_ids, datas, location_id):
        if product_ids:
            inventory = env['stock.inventory'].create({
                'name': 'auto_inventory_{}'.format(tool.format_date(datetime.datetime.now())),
                'location_ids': [(6, 0, [location_id.id])] if location_id else False,
                'date': datetime.datetime.now(),
                'product_ids': [(6, 0, product_ids)],
                'prefill_counted_quantity': 'zero',
                "company_id": location_id.company_id.id if location_id else env.company.id,
                'line_ids': self._build_inventory_lines(env, datas, location_id)
            })
            inventory.action_start()
            return inventory
        return False

    def _build_inventory_lines(self, env, datas, location_id):
        product_obj = env['product.product']
        inventory_lines = []
        for data in datas:
            product_id = data.get('product_id', False)
            quantity = data.get('quantity', 0)
            if quantity is None or not quantity:
                quantity = 0
            if product_id:
                inventory_lines.append((0, 0, {
                    'company_id': env.company.id,
                    'product_id': product_id.id,
                    'theoretical_qty': product_obj.get_theoretical_quantity(product_id.id, location_id.id),
                    'location_id': location_id.id,
                    'product_qty': 0 if int(quantity) <= 0 else quantity,
                    'product_uom_id': product_id.uom_id.id if product_id.uom_id else False,
                }))
        return inventory_lines
