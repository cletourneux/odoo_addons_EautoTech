# -*- coding: utf-8 -*-

import logging
import datetime

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from .. import tool

_logger = logging.getLogger(__name__)


class ConnectorInstance(models.Model):
    _name = 'connector.instance.eat'
    _description = "Connector Instance"

    name = fields.Char('Name', required=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft', 'Not Confirmed'), ('done', 'Confirmed')], string='Status', index=True,
                             readonly=True, copy=False, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True)
    # endpoint
    endpoint_id = fields.Many2one('process.endpoint.eat', 'Endpoint')
    # warehouse
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    user_id = fields.Many2one('res.users', string='Salesperson')
    # mapping instance warehouse
    instance_location_name = fields.Char(string='Instance Location Name', help='Mapping to connector location name')
    instance_location_id = fields.Char(string='Instance Location Id', readonly=True, help='No need input, mapping with location name')
    # fee product
    fee_product = fields.Many2one('product.product', string='Fee Product', required=True)
    # tax product
    tax_product = fields.Many2one('product.product', string='Tax Product')
    # coupon or discount product
    coupon_product = fields.Many2one('product.product', string='Coupon Product')
    # shopify can add special line item, we can use a product to mapping
    customize_product = fields.Many2one('product.product', string="Customize Product", required=True)
    # process start date
    process_start_date = fields.Datetime(string="Start Process Date", required=True)
    process_period = fields.Float(string="Process Period", required=True)
    # variant creation(create product instead of variant mapping)
    variant_creation = fields.Boolean('Variant Creation', default=True, help="For Product mapping, don't need create variant in Odoo.")
    delivery_carrier_id = fields.Many2one('delivery.carrier')
    delivery_endpoint_id = fields.Many2one('process.endpoint.eat', 'Delivery Endpoint')
    # process way
    product_process = fields.Selection([('import', 'Import'), ('export', 'Export')], string='Product Process')
    inventory_process = fields.Selection([('import', 'Import'), ('export', 'Export')], string='Inventory Process')
    order_process = fields.Selection([('import', 'Import'), ('export', 'Export')], string='Order Process')
    shipment_process = fields.Selection([('import', 'Import'), ('export', 'Export')], string='Shipment Process')
    invoice_process = fields.Selection([('import', 'Import'), ('export', 'Export')], string='Invoice Process')
    auto_confirm_order = fields.Boolean('Confirm Order')
    # account
    invoice_tax_account_id = fields.Many2one('account.account', string='Invoice Tax Account')
    credit_tax_account_id = fields.Many2one('account.account', string='Credit Tax Account')

    def button_confirm(self):
        for instance in self:
            if not instance.endpoint_id:
                raise UserError("Please set endpoint for instance.")
            instance.endpoint_id.button_confirm(instance)
            if instance.delivery_endpoint_id:
                instance.delivery_endpoint_id.button_confirm(instance)
            instance.write({'state': 'done'})
        return True

    def button_draft(self):
        for instance in self:
            instance.write({'state': 'draft'})
        return True

    def run_instance(self):
        for instance in self:
            if instance.state == 'draft':
                raise UserError('Please confirm the instance.')
            new_ctx = dict(self.env.context)
            new_ctx['allowed_company_ids'] = [instance.company_id.id]
            new_self = self.with_context(new_ctx)
            process_configs = self.env['process.config.eat'].search([('instance_id.id', '=', instance.id)])
            for process_config in process_configs:
                process_protocol = process_config.process_protocol
                process_model = process_protocol.process
                process_id = '{}-{}'.format(process_config.id, tool.format_date(tool.date_now(), '%Y%m%dT%H%M%S'))
                try:
                    _logger.info('{} processing start {}'.format(process_config.name, process_id))
                    new_self.env[process_model].process(new_self.env, process_config, process_id)
                    new_self.env.cr.commit()
                    _logger.info('{} processing end {}'.format(process_config.name, process_id))
                except Exception as e:
                    new_self.env.cr.rollback()
                    _logger.info("{} process failure {}, please check error".format(process_config.name, process_id),
                                 exc_info=True)

    def run_all(self):
        instances = self.env['connector.instance.eat'].sudo().search([('state', '=', 'done')])
        _logger.info('Connector instance running, count {}'.format(len(instances)))
        instances.run_instance()
