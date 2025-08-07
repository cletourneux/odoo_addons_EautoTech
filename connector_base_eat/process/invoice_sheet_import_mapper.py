# -*- coding: utf-8 -*-

import logging
from .. import tool
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


def date_convert(value):
    return tool.parse_date(value)


##
# <Invoice>
#   <Order></Order>
#   <InvoiceDate></InvoiceDate>
#   <AllInOne></AllInOne>
#   <InvoiceLines>
#       <InvoiceLine>
#           <Product><Product>
#           <Quantity></Quantity>
#       </InvoiceLine>
#   </InvoiceLines>
# </Invoice>
# #
class InvoiceImportMapper(models.AbstractModel):
    _name = "mapper.invoice.sheet.import.eat"
    _inherit = "mapper.import.eat"
    _description = "Invoice Mapper"

    def map_object(self, env, source, process_config):
        return tool.object_map_object([
            ('Invoice Id', 'invoice_id'), ('Client Order Id', 'client_order_id'),
            ('Invoice Date', 'invoice_date', date_convert)], source)
