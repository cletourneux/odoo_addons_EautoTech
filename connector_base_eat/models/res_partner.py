# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError


class Partner(models.Model):
    _inherit = 'res.partner'

    client_partner_id = fields.Char(string="Client Partner ID")
