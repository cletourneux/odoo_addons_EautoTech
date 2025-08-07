# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class ImportMapper(models.AbstractModel):
    _name = "mapper.import.eat"
    _inherit = "mapper.eat"
    _description = "Import Mapper"

    def map(self, env, source, process_config):
        """
        TODO we need to check the response, might be list
        :param env:
        :param source:
        :param process_config:
        :return:
        """
        process_protocol = process_config.process_protocol
        mapper = process_protocol.mapper
        if isinstance(source, (tuple, list)):
            result = []
            adjust_map_result = mapper.type in ('xlsx', 'csv')
            for item in source:
                map_object = self.map_object(env, item, process_config)
                if not map_object:
                    continue
                if adjust_map_result:
                    result.append(map_object)
                else:
                    result.append(self.adjust_object(env, map_object, process_config))
            if adjust_map_result:
                return self.adjust_map_result(env, result, process_config)
            else:
                return result
        else:
            return self.adjust_object(env, self.map_object(env, source, process_config), process_config)

    def map_object(self, env, source, process_config):
        #
        # single object mapping
        #
        raise NotImplementedError()

    def adjust_object(self, env, map_object, process_config):
        # we are sure there is one line for the object
        return map_object

    def adjust_map_result(self, env, result, process_config):
        # special case for the excel, csv, we have the case like, need get the rows, then can merge the data
        # order, order line
        # 1000, 1
        # 1000, 2
        # 1001, 1
        return result
