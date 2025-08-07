# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    _inherit = "product.pricelist.item"

    def write(self, vals):
        val_keys = vals.keys()
        product_tmpl_id = self._get_product_id(self)
        if 'fixed_price' in val_keys and product_tmpl_id:
            self.env['product.template.instance.eat'].search(
                [('product_tmpl_id.id', '=', product_tmpl_id.id)]).write({'write_date': datetime.datetime.utcnow()})
        super(ProductPricelist, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProductPricelist, self).create(vals_list)
        for record in records:
            product_tmpl_id = self._get_product_id(record)
            if product_tmpl_id:
                self.env['product.template.instance.eat'].search(
                    [('product_tmpl_id.id', '=', product_tmpl_id.id)]).write({'write_date': datetime.datetime.utcnow()})
        return records

    def _get_product_id(self, record):
        product_tmpl_id = False
        if record.applied_on == '1_product':
            product_tmpl_id = self.product_tmpl_id
        elif record.applied_on == '0_product_variant':
            product_tmpl_id = self.product_id.product_tmpl_id
        return product_tmpl_id
