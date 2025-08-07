# -*- coding: utf-8 -*-

import logging
import base64

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


def empty_convert(source):
    return source


class ProcessProcess(models.AbstractModel):
    _name = 'process.process.eat'
    _description = "Process"

    def process(self, env, process_config, process_id):
        raise NotImplementedError()

    def map(self, env, process_config, source):
        process_protocol = process_config.process_protocol
        process_type = process_protocol.process_type
        mapper = process_protocol.mapper
        mapper_model_name = mapper.model_name
        # mapper mapping is not required, such as we can customize special business(the shopify,
        # mapping is a little complex, there is not the structure as mapping define) for mapper
        # convert to target object, all should be the python object
        # such as json to python object, xml to python object
        mapper_type = mapper.type
        convert = empty_convert
        if process_type == 'import':
            source = tool.CONVERT_DICT['{}_'.format(mapper_type)](source)
        else:
            convert = tool.CONVERT_DICT['_{}'.format(mapper_type)]
        return convert(
            self.excel_csv_map_adjust(
                env[mapper_model_name].map(env, source, process_config)))

    def excel_csv_map_adjust(self, result):
        # if there is excel/csv, we need generate the sub items,
        # such as we export the order, we need generate the order lines
        return result

    def backend(self, env, process_config):
        endpoint = process_config.endpoint_id or process_config.instance_id.endpoint_id
        if endpoint:
            endpoint_type = endpoint.type
            endpoint_model = 'process.endpoint.{}.eat'.format(endpoint_type)
            config = env[endpoint_model].search([('id', '=', endpoint.id)])
            return self.customize_backend(env, endpoint_type, config)
        else:
            return False

    def customize_backend(self, env, endpoint_type, endpoint_config):
        return False

    def build_log_object(self, instance_id, log_type, process_id, comment=False, file=False, file_name=False):
        if file:
            encode_content = base64.b64encode(file)
        else:
            encode_content = False
        return {'instance_id': instance_id, 'type': log_type, 'process_id': process_id, 'comment': comment,
                'file': encode_content, 'file_name': file_name}

    def create_log(self, env, log):
        env['process.log.eat'].create(log)

    def now(self):
        return tool.date_now()

    def before_one_hour(self):
        return tool.date_before_hours(1)

    def before_hours(self, hours=0.1):
        return tool.date_before_hours(hours)

    def calc_prop_to_date(self, last_sync_date, expected_sync_date, days):
        calc_sync_date = tool.plus_days(last_sync_date, days)
        curr_sync_time = expected_sync_date
        if calc_sync_date < expected_sync_date:
            curr_sync_time = calc_sync_date
        return curr_sync_time

    def zone_now_fmt(self, env, value, zone, fmt):
        return tools.misc.format_datetime(env, value, zone, fmt)

    def flush_process_date(self, env, process_config, date):
        process_config['last_process_date'] = date

    def get_sequence(self, env, seq_name='eat.sequence'):
        return env['ir.sequence'].next_by_code(seq_name)
