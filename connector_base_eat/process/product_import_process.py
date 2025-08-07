# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class ProductImportProcess(models.AbstractModel):
    _name = "process.product.import.eat"
    _inherit = "process.import.eat"
    _description = "Product Import process"

    # TODO we also need the vendor/status/product type/category import
    def do_save_record(self, env, process_config, data):
        instance_id = process_config.instance_id
        product_tmpl_ids = self._update_product_template(env, process_config, data)
        for product_tmpl_id in product_tmpl_ids:
            product_variants = self._mapping_product_variant(env, process_config, data, product_tmpl_id)
            self._product_instance_ref(env, data, instance_id, product_tmpl_id, product_variants)
        return False

    def _update_product_template(self, env, process_config, data):
        """
        :param env:
        :param process_config:
        :param data:
        :return: template ids
        """
        product_tmpl_obj = env['product.template']
        # if no variant, we just create the template, on product variant will be created automatically
        if data.get('no_variant', '') == '1':
            variant = data['variants'][0]
            return [self._create_product_template(env, product_tmpl_obj, process_config, data, variant)]
        else:
            instance_id = process_config.instance_id
            if instance_id.variant_creation:
                return [self._create_product_variant(env, product_tmpl_obj, process_config, data)]
            else:
                variants = data['variants']
                product_tmpl_ids = []
                for variant in variants:
                    product_tmpl_ids.append(self._create_product_template(
                        env, product_tmpl_obj, process_config, data, variant))
                return product_tmpl_ids

    def _create_product_variant(self, env, product_tmpl_obj, process_config, data):
        instance_product_id = data['instance_product_id']
        instance_id = process_config.instance_id
        product_tmpl_instance_id = env['product.template.instance.eat'].search(
            [('instance_id.id', '=', instance_id.id), ('instance_product_id', '=', instance_product_id)])
        product_tmpl_id = product_tmpl_instance_id.product_tmpl_id if product_tmpl_instance_id else False
        attribute_line_ids = self._build_product_tmpl_attributes(env, data, product_tmpl_id)
        product_tmpl_val = self.build_product_model(env, process_config, data, product_tmpl_id)
        product_tmpl_val['attribute_line_ids'] = attribute_line_ids
        # there would be the issue ("Incompatible companies on records:\\n- \'[32008A11] Antarctic 32008A\'
        # belongs to company False and \'Responsible\' (responsible_id: \'OdooBot\') belongs to another company.", \'\')
        product_tmpl_val['responsible_id'] = False
        if product_tmpl_id:
            product_tmpl_id.write(product_tmpl_val)
            return product_tmpl_id
        else:
            return product_tmpl_obj.create(product_tmpl_val)

    def _create_product_template(self, env, product_tmpl_obj, process_config, data, variant):
        product_tmpl_id = product_tmpl_obj.search([('default_code', '=', variant['reference'])], limit=1)
        # need also check the variant
        if not product_tmpl_id:
            product_variant_id = env['product.product'].search([('default_code', '=', variant['reference'])], limit=1)
            if product_variant_id:
                product_tmpl_id = product_variant_id.product_tmpl_id
        product_tmpl_val = self.build_product_model(env, process_config, data, product_tmpl_id)
        # there would be the issue ("Incompatible companies on records:\n- '[----] ---'
        # belongs to company False and 'Responsible' (responsible_id: 'OdooBot') belongs to another company.", '')
        product_tmpl_val['responsible_id'] = False
        if product_tmpl_id:
            product_tmpl_id.write(product_tmpl_val)
        else:
            # for creation we need, or we skip, clear the barcode
            if variant['barcode']:
                barcode_variant_id = env['product.product'].search([('barcode', '=', variant['barcode'])], limit=1)
                if barcode_variant_id:
                    barcode_variant_id.write({'barcode': False})
            product_tmpl_val.update({'default_code': variant['reference'], 'barcode': variant['barcode']})
            product_tmpl_id = product_tmpl_obj.create(product_tmpl_val)
        return product_tmpl_id

    def build_product_model(self, env, process_config, data, product_tmpl_id):
        return {
            'name': data['name'],
            'description': data['description'],
            'type': 'consu',
        }

    def _mapping_product_variant(self, env, process_config, data, product_template):
        instance_id = process_config.instance_id
        product_attribute_obj = env['product.attribute']
        product_attribute_value_obj = env['product.attribute.value']
        product_template_attribute_value_obj = env['product.template.attribute.value']
        product_variant_obj = env['product.product']
        product_variants = []
        for variant in data['variants']:
            reference = variant['reference']
            barcode = variant['barcode']
            price = variant['price']
            variant_attributes = variant.get('attr_values', {})
            domain = []
            template_attribute_value_ids = []
            for attribute_name, attribute_val in variant_attributes.items():
                product_attribute = product_attribute_obj.search([('name', '=ilike', attribute_name)], limit=1)
                product_attribute_value = False
                if product_attribute:
                    product_attribute_value = product_attribute_value_obj.search(
                        [('attribute_id', '=', product_attribute.id), ('name', '=', str(attribute_val))], limit=1)
                if product_attribute_value:
                    template_attribute_value_id = product_template_attribute_value_obj.search(
                        [('product_attribute_value_id', '=', product_attribute_value.id),
                         ('attribute_id', '=', product_attribute.id), ('product_tmpl_id', '=', product_template.id)],
                        limit=1)
                    template_attribute_value_id and template_attribute_value_ids.append(template_attribute_value_id.id)
            # this can't use the in, we need all should equal the value
            for template_attribute_value in template_attribute_value_ids:
                domain.append(('product_template_attribute_value_ids.id', '=', template_attribute_value))
            domain.append(('product_tmpl_id.id', '=', product_template.id))
            product_variant = False
            if domain:
                # we need double check the variant if we don't have multiple variants, just template ref variant
                if instance_id.variant_creation:
                    product_variant = product_variant_obj.search(domain, limit=1)
                else:
                    domain.append(('default_code', '=', reference))
                    product_variant = product_variant_obj.search(domain, limit=1)
            if product_variant:
                product_variant.write({'default_code': reference})
                product_variants.append((variant, product_variant))
                if barcode:
                    existing_barcode_product = product_variant_obj.search([('barcode', '=', barcode)], limit=1)
                    if existing_barcode_product and existing_barcode_product.id != product_variant.id:
                        # reset the old barcode with False
                        existing_barcode_product.write({'barcode': False})
                    else:
                        product_variant.write({'barcode': barcode})
                if price:
                    # price list or detail price setting for list price
                    pricelist_id = instance_id.pricelist_id
                    if pricelist_id:
                        price_item = self.env['product.pricelist.item'].search(
                            [('pricelist_id.id', '=', pricelist_id.id), ('product_id.id', '=', product_variant.id)],
                            limit=1)
                        if price_item:
                            price_item['fixed_price'] = price
                        else:
                            self.env['product.pricelist.item'].create({
                                'applied_on': '0_product_variant',
                                'min_quantity': 1,
                                'product_id': product_variant.id,
                                'compute_price': 'fixed',
                                'fixed_price': price,
                                'pricelist_id': pricelist_id.id,
                            })
        return product_variants

    def _build_product_tmpl_attributes(self, env, data, product_tmpl_id):
        ##
        # 1. attribute not existing, just create all
        # 2. update the attributes,(remove or add), ignore the case remove
        # #
        product_attr_obj = env['product.attribute']
        product_attr_line_obj = env['product.template.attribute.line']
        product_attr_val_obj = env['product.attribute.value']
        attrib_line_vals = []
        for attrib in data['attributes']:
            attrib_name = attrib.get('name')
            attrib_values = attrib.get('values')
            attribute = product_attr_obj.search([('name', '=ilike', attrib_name)], limit=1)
            if not attribute:
                attribute = product_attr_obj.create({'name': attrib_name})
            attr_val_ids = []
            for attrib_vals in attrib_values:
                attrib_value = product_attr_val_obj.search(
                    [('attribute_id', '=', attribute.id), ('name', '=', str(attrib_vals))], limit=1)
                if not attrib_value:
                    attrib_value = product_attr_val_obj.with_context(active_id=False).create(
                        {'attribute_id': attribute.id, 'name': attrib_vals})
                    attr_val_ids.append(attrib_value.id)
                else:
                    if product_tmpl_id:
                        product_attr_line = product_attr_line_obj.search([('product_tmpl_id', '=', product_tmpl_id.id),('attribute_id', '=', attribute.id), ('value_ids.id', '=', attrib_value.id)])
                        if not product_attr_line:
                            attr_val_ids.append(attrib_value.id)
                    else:
                        attr_val_ids.append(attrib_value.id)
            if attr_val_ids:
                attribute_line_ids_data = [0, False,
                                           {'attribute_id': attribute.id, 'value_ids': [[6, False, attr_val_ids]]}]
                attrib_line_vals.append(attribute_line_ids_data)
        return attrib_line_vals

    def _product_instance_ref(self, env, data, instance_id, product_tmpl_id, variants):
        instance_product_id = data['instance_product_id']
        product_tmpl_instance_id = env['product.template.instance.eat'].search(
            [('instance_id.id', '=', instance_id.id), ('instance_product_id', '=', instance_product_id)])
        tmpl_instance = {
            'product_tmpl_id': product_tmpl_id.id,
            'instance_id': instance_id.id,
            'instance_product_id': instance_product_id
        }
        if not product_tmpl_instance_id:
            env['product.template.instance.eat'].create(tmpl_instance)
        else:
            product_tmpl_instance_id.write(tmpl_instance)
        for variant, odoo_variant in variants:
            client_product_ref = variant['instance_product_id']
            inventory_item_id = variant.get('inventory_item_id', False)
            product_instance_id = env['product.product.instance.eat'].search([
                ('instance_id.id', '=', instance_id.id), ('instance_product_id', '=', client_product_ref)])
            variant_instance = {
                'product_id': odoo_variant.id,
                'instance_id': instance_id.id,
                'instance_product_id': client_product_ref,
                'instance_inventory_id': inventory_item_id,
                'track_quantity': variant['track_quantity'],
                'selling_without_stock': variant['selling_without_stock'],
            }
            if not product_instance_id:
                env['product.product.instance.eat'].create(variant_instance)
            else:
                product_instance_id.write(variant_instance)
