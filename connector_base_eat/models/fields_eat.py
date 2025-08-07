# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


old_update_db_foreign_key = fields.Many2one.update_db_foreign_key


def update_db_foreign_key(self, model, column):
    comodel = model.env[self.comodel_name]
    if comodel._table == 'process_endpoint_eat':
        return
    else:
        old_update_db_foreign_key(self, model, column)


fields.Many2one.update_db_foreign_key = update_db_foreign_key
