# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class InventorySheetImportMapper(models.AbstractModel):
    _name = "mapper.inventory.sheet.import.eat"
    _inherit = "mapper.import.eat"
    _description = "Inventory Mapper"

    def map_object(self, env, source, process_config):
        return tool.object_map_object([
            ('Client Inventory Id', 'client_inventory_id'), ('Product Reference', 'product_reference'),
            ('Quantity', 'quantity')], source)
