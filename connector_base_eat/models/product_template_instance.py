# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductTemplateInstance(models.Model):
    _name = 'product.template.instance.eat'
    _description = "Product Template Instance"

    product_tmpl_id = fields.Many2one('product.template', 'Product Template', required=True)
    instance_id = fields.Many2one('connector.instance.eat', required=True)
    instance_product_id = fields.Char('Instance Product ID')
