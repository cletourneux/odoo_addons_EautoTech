# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class Endpoint(models.Model):
    _name = 'process.endpoint.eat'
    _description = "Process Endpoint"

    name = fields.Char(string='Name', translate=True)
    type = fields.Char(string='Type')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Endpoint, self).create(vals_list)
        # self.get_bindings() depends on action records
        self.clear_caches()
        return res

    def write(self, vals):
        res = super(Endpoint, self).write(vals)
        # self.get_bindings() depends on action records
        self.clear_caches()
        return res

    def unlink(self):
        res = super(Endpoint, self).unlink()
        # self.get_bindings() depends on action records
        self.clear_caches()
        return res

    def get_target_endpoint(self):
        self.ensure_one()
        endpoint_type = self.type
        endpoint_model = 'process.endpoint.{}.eat'.format(endpoint_type)
        return self.env[endpoint_model].search([('id', '=', self.id)])

    def button_confirm(self, instance):
        """
        must implement in child, or will call parent, it would be wrong
        confirm the target endpoint
        :param instance:
        :return:
        """
        for endpoint in self:
            config = endpoint.get_target_endpoint()
            config.init_check(instance)
            config.setup_process_config(instance)
        return True

    def init_check(self, instance):
        pass

    def init_process_configs(self, instance):
        return ()

    def current_module_name(self):
        return 'connector_base_eat'

    def skip_active_process_config(self):
        """
        skip the process config setting, for the delivery, we need think another way
        :return:
        """
        return False

    def setup_process_config(self, instance):
        self._create_process_config(instance)
        if not self.skip_active_process_config():
            self._active_process_config(instance)

    def _create_process_config(self, instance):
        process_items = self.init_process_configs(instance)
        endpoint = self
        process_date = instance.process_start_date
        for source_process_item in process_items:
            process_item = dict(source_process_item)
            process = process_item.pop('process')
            # check if we have existing items, skip for creation
            process_id = self.env['ir.model.data']._xmlid_lookup('{}.{}'.format(self.current_module_name(), process))[1]
            existing_process_item = self.env['process.config.eat'].search_count([('instance_id.id', '=', instance.id),
                ('process_protocol', '=', process_id), '|',  ('active', '=', False), ('active', '=', True)])
            if not existing_process_item:
                process_item['endpoint_id'] = endpoint.id
                process_item['instance_id'] = instance.id
                process_item['process_protocol'] = process_id
                process_item['last_process_date'] = process_date
                self.env['process.config.eat'].create(process_item)

    def _active_process_config(self, instance):
        self._update_process_config(instance, 'product', instance.product_process)
        self._update_process_config(instance, 'inventory', instance.inventory_process)
        self._update_process_config(instance, 'order', instance.order_process)
        self._update_process_config(instance, 'shipment', instance.shipment_process)
        self._update_process_config(instance, 'invoice', instance.invoice_process)

    def _update_process_config(self, instance, business_type, process_type):
        """
        we need the active and inactive, if we didn't set the process type, just disabled the transfer
        :param instance:
        :param business_type:
        :param process_type:
        :return:
        """
        active = True if process_type == 'import' else False
        inactive = not active
        if not process_type:
            active = False
            inactive = False
        self.env['process.config.eat'].search(
            [('instance_id.id', '=', instance.id), ('business_type', '=', business_type),
             ('endpoint_id.id', '=', self.id), ('process_type', 'in', ('import', 'feed')), '|',
             ('active', '=', False), ('active', '=', True)]).write({'active': active})
        self.env['process.config.eat'].search(
            [('instance_id.id', '=', instance.id), ('business_type', '=', business_type),
             ('endpoint_id.id', '=', self.id), ('process_type', '=', 'export'), '|',
             ('active', '=', False), ('active', '=', True)]).write({'active': inactive})
