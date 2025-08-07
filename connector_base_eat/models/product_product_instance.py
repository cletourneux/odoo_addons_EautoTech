# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductProductInstance(models.Model):
    _name = 'product.product.instance.eat'
    _description = "Product Instance"

    product_id = fields.Many2one('product.product', 'Product', required=True)
    instance_id = fields.Many2one('connector.instance.eat', required=True)
    instance_product_id = fields.Char('Instance Product ID')
    instance_inventory_id = fields.Char('Instance Inventory ID')
    track_quantity = fields.Boolean('Track Quantity')
    selling_without_stock = fields.Boolean('Selling without Stock')
    manual_inventory = fields.Boolean('Manual Inventory')
    shopify_manual_inventory = fields.Boolean('Shopify Manual Inventory')
