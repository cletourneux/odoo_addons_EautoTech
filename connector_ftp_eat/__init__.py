# -*- coding: utf-8 -*-

from . import models
from . import backend
from . import process
from . import wizard


def create_required_table(env):
    env.cr.execute("CREATE TABLE process_endpoint_ftp_eat (primary key(id)) INHERITS (process_endpoint_eat);")
    env.cr.execute("CREATE TABLE process_endpoint_sftp_eat (primary key(id)) INHERITS (process_endpoint_eat);")
