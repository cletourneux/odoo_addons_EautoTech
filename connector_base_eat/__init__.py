# -*- coding: utf-8 -*-

from . import tool
from . import models
from . import backend
from . import process
from . import wizard
from . import controller


def create_required_table(env):
    env.cr.execute("CREATE TABLE process_endpoint_eat (id serial, primary key(id));")


# def remove_useless_foreign_key(cr, registry):
#     # remove the INHERITS table, db support INHERITS table but can't support foreign key
#     from odoo import tools
#     tools.drop_constraint(cr, 'connector_instance_eat', 'connector_instance_eat_endpoint_id_fkey')
#     tools.drop_constraint(cr, 'process_config_eat', 'process_config_eat_endpoint_id_fkey')
