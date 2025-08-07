# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class InventoryExportProcess(models.AbstractModel):
    _name = "process.inventory.export.eat"
    _inherit = "process.export.eat"
    _description = "Inventory Export process"

    def build_data_list(self, env, process_config, now):
        domains = self.build_domain(env, process_config, now)
        domains.append(('instance_id.id', '=', process_config.instance_id.id))
        domains.append(('track_quantity', '=', True))
        # manual manage inventory
        domains.append(('manual_inventory', '=', False))
        product_instances = env['product.product.instance.eat'].search(domains)
        inventory_type = process_config.get_property('inventory_type')
        warehouse = process_config.instance_id.warehouse_id
        product_obj = env['product.product'].with_context(company_id=warehouse.company_id.id)
        product_ids = product_instances.mapped('product_id')
        if product_ids:
            if inventory_type == 'qty_available':
                product_stock_dict = product_obj.get_product_qty_by_warehouse(product_ids.ids, warehouse.id, True)
            else:
                product_stock_dict = product_obj.get_product_qty_by_warehouse(product_ids.ids, warehouse.id, False)
        else:
            product_stock_dict = {}
        self.adjust_quantity(env, process_config, product_stock_dict)
        result = []
        for product_instance in product_instances:
            product = product_instance.product_id
            result_object = {'db_id': product_instance.id, 'reference': product.default_code,
                             'quantity': product_stock_dict.get(product.id, 0),
                             'client_inventory_id': product_instance.instance_inventory_id}
            self.adjust_result_object(env, process_config, result_object, product_instance)
            result.append(result_object)
        return result

    def adjust_result_object(self, env, process_config, result_object, product_instance):
        pass

    def adjust_quantity(self, env, process_config, product_stock_dict):
        """
        make the inventory inherit to adjust other business, such as we have kit inventory
        :param env:
        :param process_config:
        :param product_stock_dict:
        :return:
        """
        pass
