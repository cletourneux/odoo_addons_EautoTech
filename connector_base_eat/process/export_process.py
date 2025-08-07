# -*- coding: utf-8 -*-

import logging
import json

from odoo import api, fields, models, tools, _
from odoo.tools.safe_eval import safe_eval
from .. import tool

_logger = logging.getLogger(__name__)


class ExportProcess(models.AbstractModel):
    _name = "process.export.eat"
    _inherit = "process.process.eat"
    _description = "Export Data process"

    def process(self, env, process_config, process_id):
        now = self.now()
        # we can have a idea, if the last process date with now is very big, we could think split the date to make the
        # system effective, default is one week
        last_process_date = process_config.last_process_date or now
        diff_days = tool.date_diff_days(last_process_date, now)
        if diff_days > 7:
            now = tool.plus_days(last_process_date, 7)
        result = self.do_process(env, process_config, now)
        if result:
            process_config['last_process_date'] = now

    def do_process(self, env, process_config, now):
        source = self.build_data_list(env, process_config, now)
        # double check if we have data, or just return
        if not source:
            return True
        data = self.map(env, process_config, source)
        result, errors = self.do_export(env, process_config, data)
        self.do_source_callback(env, process_config, source)
        return self.do_success_process(env, process_config, data, result) \
               and self.do_fail_process(env, process_config, data, errors)

    def do_success_process(self, env, process_config, data, result):
        """
        we handle the success process, such as for shopify, we don't the product export, we need do local data relation
        :param env:
        :param process_config:
        :param data:
        :param result:
        :return:
        """
        return True

    def do_fail_process(self, env, process_config, data, result):
        """
        we should be care for the error situation, if there is a batch process, we just rollback the failure items,
        we can continue submit the correct items
        :param env:
        :param process_config:
        :param data:
        :param result:
        :return:
        """
        return True

    def do_source_callback(self, env, process_config, source):
        """
        if we finish the order sending, such as shipping, we need change the status
        :param env:
        :param process_config:
        :param source: source data
        :return:
        """
        return True

    def build_data_list(self, env, process_config, now):
        return []

    def do_export(self, env, process_config, data):
        return [], []

    def build_domain(self, env, process_config, now):
        # special domain for export
        domain = process_config.get_property('domain')
        process_way = process_config.process_way
        domains = domain and safe_eval(domain) or []
        last_process_date = process_config.last_process_date
        if process_way == 'last_update':
            domains.append(('write_date', '<=', now))
            domains.append(('write_date', '>', last_process_date))
        elif process_way == 'create':
            domains.append(('create_date', '<=', now))
            domains.append(('create_date', '>', last_process_date))
        return domains
