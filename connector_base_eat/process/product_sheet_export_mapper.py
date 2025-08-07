# -*- coding: utf-8 -*-

import logging
import json
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ProductSheetExportMapper(models.AbstractModel):
    _name = "mapper.product.sheet.export.eat"
    _inherit = "mapper.eat"
    _description = "Product Sheet Export Mapper"

    def map(self, env, source, process_config):
        result = []
        mapping_items = [
            ('reference', 'Variant/Product Reference'), ('lst_price', 'Variant/Price'),
            ('instance_product_id', 'Variant/Client Product Variant Id'), ('barcode', 'Variant/Barcode')]
        for product in source:
            variants = product['variants']
            client_ref = product['instance_product_id']
            attributes = json.dumps(product['attributes'])
            for variant in variants:
                target_product = {'Client Product Id': client_ref, 'Product Name': product['name'],
                                  'Sale Description': product['description'], 'Attributes': attributes}
                target_product = tool.object_map_object_default(mapping_items, variant, target_product)
                # set variant values
                target_product['Variant/AttrValues'] = json.dumps(variant['attr_values'])
                result.append(target_product)
        return result
