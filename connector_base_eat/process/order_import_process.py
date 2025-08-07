# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, tools, _
from .. import tool

_logger = logging.getLogger(__name__)


class OrderImportProcess(models.AbstractModel):
    """
    status: open, closed, cancelled
    financial_status: pending, paid, refunded, partially_refunded
    fulfillment_status: pending, shipped
    refund item
    item: order line item
    shipping: shipping price
    adjust: amount adjust
    refund_items = [
        type: ['item', 'shipping', 'adjust'],
        product:
        description:
        quantity:
        subtotal:
        total_tax:
        date:
        line_id:
    ]

    order_items = [
    type: ['item', 'shipping', 'tax', 'discount']
    product:
    name:
    quantity:
    unit_price:
    line_id:
    discount: # line discount, there is also discount(with discount code) for order
    tax_lines: [
        name,
        rate,
        price,
        tax_included [default is False]

        ]
    ]

    """
    _name = "process.order.import.eat"
    _inherit = "process.import.eat"
    _description = "Order Import process"

    def do_save_record(self, env, process_config, data):
        # check the client order ref
        client_order_ref = data.get('client_order_ref', False)
        params = self.init_order_process_param(env, process_config, data)
        if client_order_ref:
            order = env['sale.order'].search([('client_order_ref', '=', client_order_ref),
                                              ('instance_id.id', '=', process_config.instance_id.id),
                                              ('active', 'in', (True, False))], limit=1)
            if order:
                params['exists'] = True
                self.do_order_process(env, process_config, data, order, **params)
                return False
        partner_id, shipping_id, invoice_id = self.create_address(env, process_config, data)
        data['partner_id'] = partner_id.id
        data['partner_shipping_id'] = shipping_id.id
        data['partner_invoice_id'] = invoice_id.id
        self.build_order_detail(env, process_config, data)
        self.build_order_lines(env, process_config, data)
        sale_order = env['sale.order'].create(data)
        # auto confirm
        auto_confirm_order = process_config.instance_id.auto_confirm_order
        if auto_confirm_order:
            try:
                with env.cr.savepoint():
                    sale_order.action_confirm()
            except Exception as e:
                sale_order.message_post(body=str(e))
                _logger.info('Order confirm error', stack_info=True)

            # set delivery carrier for out
            if process_config.instance_id.delivery_carrier_id:
                sale_order.picking_ids.filtered(lambda p: p.picking_type_id.code == 'outgoing').write(
                    {'carrier_id': process_config.instance_id.delivery_carrier_id.id})
                sale_order.write({'carrier_router': process_config.instance_id.delivery_carrier_id.delivery_type})
        params['exists'] = False
        self.do_order_process(env, process_config, data, sale_order, **params)
        return False

    def create_address(self, env, process_config, data):
        shipping_address = data.pop('shipping_address', False)
        invoice_address = data.pop('invoice_address', False)
        self.adjust_address_country_state(env, process_config, shipping_address)
        self.adjust_address_country_state(env, process_config, invoice_address)
        partner = data.pop('partner', False)
        if not partner:
            partner = {'name': 'please set partner setting'}
        client_partner_id = partner.pop('client_partner_id', False)
        if client_partner_id:
            partner_id = env['res.partner'].search([('client_partner_id', '=', client_partner_id)])
            if not partner_id:
                partner_id = env['res.partner'].create(partner)
            else:
                partner_id.update(partner)
        else:
            partner_id = env['res.partner'].create(partner)
        shipping_id = partner_id
        if shipping_address:
            shipping_address['parent_id'] = partner_id.id
            shipping_id = env['res.partner'].create(shipping_address)
        invoice_id = partner_id
        if invoice_address:
            invoice_address['parent_id'] = partner_id.id
            invoice_id = env['res.partner'].create(invoice_address)
        # if we have invoice address, not shipping address, use invoice address
        if invoice_address and not shipping_address:
            shipping_id = invoice_id
        # if we have shipping address, not invoice address, use shippig address
        if shipping_address and not invoice_address:
            invoice_id = shipping_id
        return partner_id, shipping_id, invoice_id

    def adjust_address_country_state(self, env, process_config, address):
        if not address:
            return
        country = address.pop('country')
        state = address.pop('state')
        if country:
            existing_country = env['res.country'].search(['|', ('name', '=', country), ('code', '=', country)], limit=1)
            if not existing_country:
                existing_country = env['res.country'].create({'name': country})
            address['country_id'] = existing_country.id
        if state:
            country_id = address['country_id']
            existing_state = env['res.country.state'].search([('name', '=', state), ('country_id.id', '=', country_id)],
                                                             limit=1)
            if not existing_state:
                existing_state = env['res.country.state'].create(
                    {'name': state, 'code': state, 'country_id': country_id})
            address['state_id'] = existing_state.id

    def init_order_process_param(self, env, process_config, data):
        """
        crate the param for the process params, these fields need to be removed, or we have the save issue
        :param env:
        :param process_config:
        :param data:
        :return:
        """
        status = data.pop('status', False)
        financial_status = data.pop('financial_status', False)
        fulfillment_status = data.pop('fulfillment_status', False)
        return {'status': status, 'financial_status': financial_status, 'fulfillment_status': fulfillment_status,}

    def do_order_process(self, env, process_config, data, sale_order, **params):
        """
        customize for order process, such as cancel order based on the status
        :param env:
        :param process_config:
        :param data:
        :param sale_order:
        :param params:
        :return:
        """
        pass

    def build_order_lines(self, env, process_config, data):
        """
        convert the order line with storable order line model
        :param env:
        :param process_config:
        :param data:
        :return:
        """
        order_line_items = []
        order_lines = data.pop('order_lines')
        instance = process_config.instance_id
        for order_line in order_lines:
            line_item = {}
            product = order_line.get('product', False)
            name = order_line.get('name', False)
            discount = order_line.get('discount', 0.0)
            if not product:
                product_id = instance.customize_product
                line_item['name'] = name
            else:
                product_id = env['product.product'].search([('default_code', '=', product)], limit=1)
                # there is issue regarding some sku was removed
                if not product_id:
                    product_id = instance.customize_product
                    _logger.info('Order {} order line product {} is not matching in system'.format(
                        data.get('client_order_ref', ''), product))
                    line_item['name'] = product
            line_item['product_id'] = product_id.id
            line_item['client_order_line_id'] = order_line['line_id']
            line_item['price_unit'] = order_line['unit_price']
            line_item['product_uom_qty'] = order_line['quantity']
            line_item['discount'] = discount
            self.build_order_line_tax(env, data, process_config, order_line, line_item)
            self.adjust_order_line(env, data, process_config, order_line, line_item)
            order_line_items.append((0, 0, line_item))
            self.adjust_main_product_line(env, data, process_config, order_line_items, line_item, order_line)
        # fee line
        fee_lines = data.pop('fee_lines', [])
        for fee_line in fee_lines:
            price = fee_line['unit_price']
            # if the price is 0, skip it
            if float(price) == 0:
                continue
            product = instance.tax_product or instance.fee_product
            if fee_line['type'] == 'discount':
                price = -float(price)
                product = instance.coupon_product or instance.fee_product
            elif fee_line['type'] == 'shipping':
                product = instance.fee_product
            order_line_items.append((0, 0, {
                'product_id': product.id,
                'name': fee_line['name'],
                'product_uom_qty': fee_line['quantity'],
                'price_unit': price
            }))
        data['order_line'] = order_line_items

    def adjust_order_line(self, env, order, process_config, line_data, order_line):
        """
        adjust order line data, we might need set required files for order line based on customized
        :param env:
        :param order:
        :param process_config:
        :param line_data: source order line data
        :param order_line: target order line
        :return:
        """
        pass

    def adjust_main_product_line(self, env, order, process_config, order_line_items, order_line, source_line):
        """
        we might need customize the other line based on sale order line(such as packaging)
        :param env:
        :param order:
        :param process_config:
        :param order_line_items:
        :param order_line: target order line
        :param source_line: source line item
        :return:
        """
        pass

    def build_order_detail(self, env, process_config, data):
        """
        set default for order if we didn't set in mapper
        :param env:
        :param process_config:
        :param data: order detail
        :return:
        """
        data['instance_id'] = process_config.instance_id.id
        if not data.get('pricelist_id', False):
            data['pricelist_id'] = process_config.instance_id.pricelist_id.id
        if not data.get('warehouse_id', False):
            data['warehouse_id'] = process_config.instance_id.warehouse_id.id
        if not data.get('user_id', False):
            data['user_id'] = process_config.instance_id.user_id.id
        if not data.get('payment_term_id', False):
            try:
                payment_term_id = env['ir.model.data']._xmlid_lookup('account.account_payment_term_immediate')[2]
                data['payment_term_id'] = payment_term_id
            except:
                _logger.info('please config the payment term account_payment_term_immediate')

    def build_order_line_tax(self, env, order, process_config,  source_order_line, order_line):
        tax_id = []
        taxes = []
        account_tax_obj = env['account.tax']
        tax_lines = source_order_line.pop('tax_lines', [])
        for tax_line in tax_lines:
            acctax_id = self._create_order_line_account_tax(env, process_config, account_tax_obj, order_line, tax_line)
            if acctax_id:
                taxes.append(acctax_id.id)
        if taxes:
            tax_id = [(6, 0, taxes)]
        return tax_id

    def _create_order_line_account_tax(self, env, process_config, account_tax_obj, order_line, tax_line):
        instance_id = process_config.instance_id
        company = instance_id.company_id
        unit_price = order_line.get('price_unit', 0)
        rate = float(tax_line.get('rate', 0.0))
        price = float(tax_line.get('price', 0.0))
        name = tax_line.get('name')
        tax_included = tax_line.get('tax_included', False)
        if rate == 0 and price > 0 and unit_price > 0:
            rate = float(price * 100 / unit_price)
        # no tax setting, skip
        if rate == 0:
            return False
        if tax_included:
            name = '{}_({}% included)_%s'.format(name, rate, company.name)
        else:
            name = '{}_({}% included)_%s'.format(name, rate, '%', company.name)
        acctax_id = account_tax_obj.search(
            [('price_include', '=', tax_included), ('type_tax_use', '=', 'sale'),
             ('amount', '=', rate), ('name', '=', name),
             ('company_id', '=', company.id)], limit=1)
        if not acctax_id:
            account_tax_id = account_tax_obj.create(
                {'name': name, 'amount': rate, 'type_tax_use': 'sale', 'price_include': tax_included,
                 'company_id': company.id})
            account_tax_id.mapped('invoice_repartition_line_ids').write(
                {'account_id': instance_id.invoice_tax_account_id.id if instance_id.invoice_tax_account_id else False})
            account_tax_id.mapped('refund_repartition_line_ids').write(
                {'account_id': instance_id.credit_tax_account_id.id if instance_id.credit_tax_account_id else False})
        return acctax_id
