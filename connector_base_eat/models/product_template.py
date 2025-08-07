# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def write(self, vals):
        val_keys = vals.keys()
        if 'name' in val_keys or 'description' in val_keys or 'attribute_line_ids' in val_keys:
            self.env['product.template.instance.eat'].search(
                [('product_tmpl_id.id', 'in', self.ids)]).write({'write_date': datetime.datetime.utcnow()})
        return super(ProductTemplate, self).write(vals)
