# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = "product.product"

    def write(self, vals):
        if len(self) == 1 and type(self.product_tmpl_id.id) != int:
            return super(Product, self).write(vals)
        val_keys = vals.keys()
        if 'list_price' in val_keys:
            template_ids = self.mapped('product_tmpl_id.id')
            self.env['product.template.instance.eat'].search(
                [('product_tmpl_id.id', 'in', template_ids)]).write({'write_date': datetime.datetime.utcnow()})
        return super(Product, self).write(vals)

    def get_qty_on_hand(self, warehouse, product_list):
        """
        This method is return On hand quantity(equal free qty) based on warehouse and product list, good performance
        without the stock move checking
        :return:
        :param warehouse: warehouse object
        :param product_list: list of product object
        :return:On hand quantity
        """
        locations = self.env['stock.location'].search([('location_id', 'child_of',
                                                        warehouse.mapped('lot_stock_id').mapped('id'))])
        location_ids = ','.join(str(e) for e in locations.ids)
        product_list_ids = ','.join(str(e) for e in product_list.ids)
        qry = """select pp.id as product_id,
                COALESCE(sum(sq.quantity)-sum(sq.reserved_quantity),0) as stock
                from product_product pp
                left join stock_quant sq on pp.id = sq.product_id and
                sq.location_id in (%s)
                where pp.id in (%s) group by pp.id;""" % (location_ids, product_list_ids)
        self._cr.execute(qry)
        return self._cr.dictfetchall()

    def get_product_qty_by_warehouse(self, ids, warehouse_id, is_free_qty=True):
        products = self.env['product.product'].with_context(warehouse_id=warehouse_id).browse(ids)
        products._compute_quantities()
        quantities = {}
        if is_free_qty:
            for product in products:
                quantities[product.id] = product.free_qty
        else:
            for product in products:
                quantities[product.id] = product.virtual_available
        return quantities

    def get_forecated_qty(self, warehouse, product_list):
        """
        This method is return forecasted quantity based on warehouse and product list, good performance
        without the stock move checking
        :param warehouse:warehouse object
        :param product_list:list of product object
        :return: Forecasted Quantity
        """
        locations = self.env['stock.location'].search([('location_id', 'child_of',
                                                        warehouse.mapped('lot_stock_id').mapped('id'))])
        location_ids = ','.join(str(e) for e in locations.ids)
        product_list_ids = ','.join(str(e) for e in product_list.ids)
        qry = """select *
                from (select pp.id as product_id,
                COALESCE(sum(sq.quantity)-sum(sq.reserved_quantity),0) as stock
                from product_product pp
                left join stock_quant sq on pp.id = sq.product_id and
                sq.location_id in (%s)
                where pp.id in (%s) group by pp.id
                union all
                select product_id as product_id,sum(product_qty) as stock from stock_move
                where state in ('assigned') and product_id in (%s) and location_dest_id in (%s)
                group by product_id) as test"""\
              % (location_ids, product_list_ids, product_list_ids, location_ids)
        self._cr.execute(qry)
        return self._cr.dictfetchall()

    def get_kit_free_qty(self, warehouse, ids):
        """
        This method is return free quantity based on warehouse and product list, the performance is not good,
        since there is full checking with in/out for the move
        :return:
        :param warehouse: warehouse object
        :param ids: list of product ids
        :return:On hand quantity
        """
        products = self.env['product.product'].with_context(warehouse_id=warehouse.id).browse(ids)
        quantities = {}
        for product in products:
            quantities[product.id] = product.free_qty
        return quantities

    def get_kit_forecast_qty(self, warehouse, ids):
        """
        This method is return forecast quantity based on warehouse and product list, the performance is not good,
        since there is full checking with in/out for the move
        :return:
        :param warehouse: warehouse object
        :param ids: list of product ids
        :return:On hand quantity
        """
        products = self.env['product.product'].with_context(warehouse_id=warehouse.id).browse(ids)
        quantities = {}
        for product in products:
            quantities[product.id] = product.virtual_available
        return quantities
