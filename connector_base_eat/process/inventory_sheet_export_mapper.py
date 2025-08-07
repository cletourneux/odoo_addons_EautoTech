# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class InventorySheetExportMapper(models.AbstractModel):
    _name = "mapper.inventory.sheet.export.eat"
    _inherit = "mapper.eat"
    _description = "Inventory Sheet Export Mapper"

    def map(self, env, source, process_config):
        result = []
        mapping_items = [
            ('reference', 'Product Reference'),
            ('quantity', 'Quantity'),
            ('client_inventory_id', 'Client Inventory Id')
        ]
        for inventory in source:
            result.append(tool.object_map_object(mapping_items, inventory))
        return result
