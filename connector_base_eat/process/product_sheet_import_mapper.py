# -*- coding: utf-8 -*-

import logging
import json
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductSheetImportMapper(models.AbstractModel):
    _name = "mapper.product.sheet.import.eat"
    _inherit = "mapper.import.eat"
    _description = "Product import Mapper"

    def map_object(self, env, source, process_config):
        product = self._build_product(env, source)
        variant = self._build_variant(env, source)
        product['variants'] = [variant]
        return product

    def adjust_object(self, env, product, process_config):
        return self.adjust_product(env, product)

    def adjust_map_result(self, env, result, process_config):
        return tool.adjust_data(env, result, self.adjust_product, 'instance_product_id', 'variants')

    def adjust_product(self, env, product):
        return product

    def _build_product(self, env, source):
        return tool.object_map_object([('Client Product Id', 'instance_product_id'), ('Name', 'name'),
               ('Sale Description', 'description'), ('Attributes', 'attributes', json.loads),
              ('No Variant', 'no_variant')], source)

    def _build_variant(self, env, source):
        return tool.object_map_object([('Variant/Product Reference', 'reference'),
             ('Variant/Price', 'price'), ('Variant/Client Product Variant Id', 'instance_product_id'),
             ('Variant/Barcode', 'barcode'), ('Variant/AttrValues', 'attr_values', json.loads)], source)
