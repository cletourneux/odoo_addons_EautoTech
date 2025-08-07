# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class Mapper(models.AbstractModel):
    _name = 'mapper.eat'
    _description = "Mapper"

    def map(self, env, source, process_config):
        raise NotImplementedError()
