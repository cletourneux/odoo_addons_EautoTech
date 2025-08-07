# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool
import json

_logger = logging.getLogger(__name__)


class ProductExportProcess(models.AbstractModel):
    _name = "process.product.export.eat"
    _inherit = "process.export.eat"
    _description = "Product Export process"

    def build_data_list(self, env, process_config, now):
        domains = self.build_domain(env, process_config, now)
        domains.append(('instance_id.id', '=', process_config.instance_id.id))
        product_instances = env['product.template.instance.eat'].search(domains)
        result = []
        for product_instance in product_instances:
            product_tmpl_id = product_instance.product_tmpl_id
            product_tmpl = self.build_product_model(env, process_config, product_instance)
            # variants
            variants = []
            product_variant_ids = env['product.product.instance.eat'].search(
                [('instance_id.id', '=', process_config.instance_id.id),
                 ('product_id.product_tmpl_id.id', '=', product_tmpl_id.id)])
            for product_instance_id in product_variant_ids:
                variant = self.build_variant_model(env, process_config, product_instance_id)
                variants.append(variant)
            product_tmpl['variants'] = variants
            product_tmpl['attributes'] = self.build_product_attributes_model(env, process_config, product_instance)
            result.append(product_tmpl)
        return result

    def build_product_model(self, env, prcess_config, product_instance):
        product_tmpl_id = product_instance.product_tmpl_id
        return {'instance_product_id': product_instance.instance_product_id, 'name': product_tmpl_id.name or '',
         'description': product_tmpl_id.description or '', 'db_id': product_instance.id,
         'type': product_tmpl_id.categ_id.complete_name or ''}

    def build_product_attributes_model(self, env, prcess_config, product_instance):
        # options
        product_tmpl_id = product_instance.product_tmpl_id
        attributes = []
        for attribute in product_tmpl_id.attribute_line_ids:
            value_ids = attribute.value_ids
            values = [value.name for value in value_ids]
            attributes.append({
                'name': attribute.attribute_id.name,
                'values': values
            })
        return attributes

    def build_variant_model(self, env, process_config, product_instance_id):
        pricelist_id = process_config.instance_id.pricelist_id
        product_id = product_instance_id.product_id
        price = product_id.lst_price
        # price list
        if pricelist_id:
            price_item = env['product.pricelist.item'].search(
                [('pricelist_id.id', '=', pricelist_id.id), ('product_id.id', '=', product_id.id)], limit=1)
            if price_item:
                price = price_item[0].fixed_price
        # vendor
        vendor = ''
        cost = 0
        if product_id.seller_ids:
            seller = product_id.seller_ids[0]
            vendor = seller.name.name
            cost = seller.price
        # attributes
        attribute_value_ids = product_id.product_template_attribute_value_ids
        variant_attributes = {}
        for attribute_value_id in attribute_value_ids:
            variant_attributes[
                attribute_value_id.attribute_id.name] = attribute_value_id.product_attribute_value_id.name
        return {
            'db_id': product_instance_id.id,
            'reference': product_id.default_code,
            'barcode': product_id.barcode,
            'lst_price': price,
            'instance_product_id': product_instance_id.instance_product_id,
            'attr_values': variant_attributes,
            'vendor': vendor, 'cost': cost, 'track_quantity': product_instance_id.track_quantity,
            'selling_without_stock': product_instance_id.selling_without_stock,
        }
