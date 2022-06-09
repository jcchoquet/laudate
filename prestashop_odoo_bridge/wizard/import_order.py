# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from xmlrpc.client import Error
import logging
import itertools
from odoo import api, fields, models, _
from odoo.exceptions import UserError,RedirectWarning, ValidationError
from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError
_logger = logging.getLogger(__name__)

OrderStatus = [
    ('0','All'),
    ('6','Canceled'),
    ('5','Shipped'),
    ('2','Complete'),
    ('12','Complete'),
    ('3','Processing'),
    ('13','On Hold'),
    ('9','Pending'),
    ('1','Pending Payment'),
    ('10','Pending Payment'),
    ('14','Pending Payment'),
    ('11','Pending Payment'),
    ('4', 'Shipped')
]

class ImportOrders(models.TransientModel):
    _inherit = ['import.orders']
    _name = 'import.prestashop.orders'
    _description = 'Import Prestashop Orders'

    status = fields.Selection(
        OrderStatus,
        required = 1,
        default = '0'
    )

    def _get_customer_name(self, prestashop, customer_id):
        name = False
        customer_email = False
        try:
            customer = prestashop.get("customers", customer_id)
            customer = customer.get("customer")
        except Exception as e:
            _logger.info("Error in getting Customers => %r",str(e))
        else:
            name = customer.get("firstname") + " " + customer.get("lastname")
            customer_email = customer.get("email")
        return {"customer_name": name, "customer_email": customer_email}

    def get_discount_line_info(self, price):
        return {
            "line_name": "Discount",
            "line_price_unit": float(price),
            "line_product_uom_qty": 1,
            "line_source": "discount",
            "line_taxes": [{
                            "rate": self.channel_id.ps_default_tax_rule_id,
                            "name": 'Tax {} % '.format(self.channel_id.ps_default_tax_rule_id),
                            "include_in_price": True if self.channel_id.default_tax_type == "include" else False,
                            "tax_type": "percent",
                        }]
        }

    def get_shipping_line_info(self,channel_id,carrier_tax_rate,shipping_price_tax_excluded,shipping_price_tax_included):
        return {
                    "line_name": "Shipping",
                    "line_price_unit": shipping_price_tax_excluded if channel_id.default_tax_type == "exclude" else shipping_price_tax_included ,
                    "line_product_uom_qty": 1,
                    "line_source" : "delivery",
                    "line_taxes": [{
                                        "rate": carrier_tax_rate,
                                        "name": 'Tax {} % '.format(carrier_tax_rate),
                                        "include_in_price": True if self.channel_id.default_tax_type == "include" else False,
                                        "tax_type": "percent",
                                    }]
                }

    def _get_order_line(self, prestashop, channel_id, order_id):
        if prestashop:
            vals_list = []
            try:
                order_detail_ids = prestashop.get('order_details',options={'filter[id_order]': order_id})
                order_detail_ids = order_detail_ids.get('order_details').get('order_detail')
                order = prestashop.get("orders",order_id)
                order = order.get("order")                
            except Exception as e:
                _logger.info("Order Details API not responding ... ====> %r",str(e))
            else:
                discount_price = order.get("total_discounts_tax_incl")
                shipping_price_tax_included = order.get("total_shipping_tax_incl")
                shipping_price_tax_excluded = order.get("total_shipping_tax_excl")
                carrier_tax_rate = order.get("carrier_tax_rate")
                if isinstance(order_detail_ids,dict):
                    order_detail_ids = order_detail_ids.get("attrs").get("id")
                    order_details = prestashop.get("order_details",order_detail_ids)
                    order_details = order_details.get("order_detail")
                    product_id = order_details.get("product_id")
                    tax_excl_price = order_details.get("unit_price_tax_excl")
                    tax_incl_price = order_details.get("unit_price_tax_incl")
                    product_attribute_id = order_details.get("product_attribute_id")
                    product_env = self.env['import.prestashop.products'].create({
                        "channel_id":channel_id.id,
                        "operation":"import"})
                    product_feed_id = product_env._prestashop_create_product_feed(
                        prestashop,product_id)
                    if product_feed_id:
                        _logger.info(
                            'Product feed with id (%r) successfully created.', product_feed_id)
                    vals = {
                                    "line_name": order_details.get("product_name"),
                                    "line_price_unit": tax_excl_price if channel_id.default_tax_type == "exclude" else tax_incl_price ,
                                    "line_product_uom_qty": order_details.get("product_quantity"),
                                    "line_product_id": product_id,
                                    "line_product_default_code": order_details.get("product_reference"),
                                    "line_variant_ids":  product_attribute_id if product_attribute_id !="0" else "No Variants"
                                }
                    taxes = order_details.get("associations").get("taxes").get("tax")
                    tax_list = []
                    if isinstance(taxes, dict):
                        id_tax = taxes.get("id")
                        vals["line_taxes"] = [self._get_product_taxes(prestashop,id_tax)]
                    elif isinstance(taxes,list):
                        tax_list = [self._get_product_taxes(prestashop, tax.get("id")) for tax in taxes]
                        vals["line_taxes"] = tax_list
                    vals_list.append((0,0,vals))
                elif isinstance(order_detail_ids,list):
                    for order_detail_id in order_detail_ids:
                        id = order_detail_id.get("attrs").get("id")
                        order_details = prestashop.get("order_details",id)
                        order_details = order_details.get("order_detail")
                        product_id = order_details.get("product_id")
                        tax_excl_price = order_details.get("unit_price_tax_excl")
                        tax_incl_price = order_details.get("unit_price_tax_incl")
                        product_attribute_id = order_details.get("product_attribute_id")
                        product_env = self.env['import.prestashop.products'].create({
                            "channel_id":channel_id.id,
                            "operation":"import"})
                        product_feed_id = product_env._prestashop_create_product_feed(
                            prestashop,product_id)
                        if product_feed_id:
                            _logger.info(
                                'Product feed with id (%r) successfully created.', product_feed_id)
                        vals = {
                                        "line_name": order_details.get("product_name"),
                                        "line_product_uom_qty": order_details.get("product_quantity"),
                                        "line_price_unit": tax_excl_price if channel_id.default_tax_type == "exclude" else tax_incl_price ,
                                        "line_product_id": product_id,
                                        "line_product_default_code": order_details.get("product_reference"),
                                        "line_variant_ids":  product_attribute_id if product_attribute_id !="0" else "No Variants"
                                    }
                        taxes = order_details.get("associations").get("taxes").get("tax")                        
                        tax_list = []                        
                        if isinstance(taxes, dict):
                            vals["line_taxes"] = [self._get_product_taxes(prestashop,taxes.get("id"))]
                        elif isinstance(taxes,list):
                            tax_list = [self._get_product_taxes(prestashop, tax.get("id")) for tax in taxes]
                            vals["line_taxes"] = tax_list

                            
                        vals_list.append((0,0,vals))
                if float(discount_price) > 0:
                    discount_line = self.get_discount_line_info(discount_price)
                    vals_list.append((0,0,discount_line))
                if shipping_price_tax_included and shipping_price_tax_excluded:
                    vals = self.get_shipping_line_info(channel_id,carrier_tax_rate,shipping_price_tax_excluded,shipping_price_tax_included)
                    vals_list.append((0,0,vals))
                return {"line_type": "multi", "line_ids": vals_list}

    def _get_product_taxes(self, prestashop, id_tax):
        vals = {}
        try:
            tax_rules = prestashop.get("taxes", id_tax)
        except Exception as e:
            _logger.info("Error :- %r",str(e))
            if self.channel_id.debug == "enable":
                raise UserError("Error while getting Taxes :- {}".format(str(e)))
        else:
            tax_rules = tax_rules.get("tax")
            names = tax_rules.get("name",{}).get("language")
            tax_name = "VAT"
            if isinstance(names,list):
                for name in names:
                    if name.get("attrs").get("id") == self.channel_id.ps_language_id:
                        tax_name = name.get("value")
                        break
            elif isinstance(names ,dict) :
                tax_name = names.get("value")
            vals = {
                "rate": float(tax_rules.get("rate")),
                "name": tax_name,
                "include_in_price": True if self.channel_id.default_tax_type == "include" else False,
                "tax_type": "percent",
            }            
        return vals

    def _get_shipping_address(self, prestashop, id_address_delivery,customer_vals):
        vals = {}
        try:
            address = prestashop.get("addresses", id_address_delivery)
        except Exception as e:
            _logger.info("Error in getting addresses ... (%r)",str(e))
        else:
            address = address.get("address")
            state_id = address.get('id_state')
            customer_id = address.get("id_customer")
            street = address.get("company") + address.get("address1")
            vals = {
                "shipping_name":address.get("firstname") + address.get("lastname"),
                "shipping_partner_id": customer_id,
                "shipping_phone": address.get("phone"),
                "shipping_mobile": address.get("phone_mobile"),
                "shipping_street": street,
                "shipping_street2": address.get("address2"),
                "shipping_zip": address.get("postcode"),
                "shipping_city": address.get("city"),
                "shipping_country_code": self._get_country_data(prestashop, address.get("id_country")),
            }
            if state_id != '0':
                state_vals = self._get_state_data(
                    prestashop, address.get("id_state"))
                vals["shipping_state_name"] = state_vals.get("state_name")
                vals["shipping_state_code"] = state_vals.get("state_code")
            vals.update(customer_vals)
        return vals

    def _get_billing_address(self, prestashop, id_address_invoice,customer_vals):
        vals = {}
        try:
            address = prestashop.get("addresses", id_address_invoice)
        except Exception as e:
            _logger.info("Error in getting addresses ...(%r)",str(e))
        else:
            address = address.get("address")
            state_id = address.get('id_state')
            customer_id = address.get("id_customer")
            street = address.get("company") + address.get("address1")
            vals = {
                "invoice_name":address.get("firstname") + address.get("lastname"),
                "invoice_partner_id": customer_id,
                "invoice_email": address.get('email',False),
                "invoice_phone": address.get("phone"),
                "invoice_mobile": address.get("phone_mobile"),
                "invoice_street": street,
                "invoice_street2": address.get("address2"),
                "invoice_zip": address.get("postcode"),
                "invoice_city": address.get("city"),
                "invoice_country_code": self._get_country_data(prestashop, address.get("id_country")),
            }
            if state_id != '0':
                state_vals = self._get_state_data(
                    prestashop, address.get("id_state"))
                vals["invoice_state_name"] = state_vals.get("state_name")
                vals["invoice_state_code"] = state_vals.get("state_code")
            vals.update(customer_vals)
        return vals

    def _get_state_data(self, prestashop, state_id):
        states = prestashop.get("states", state_id)
        state_name = states.get("state").get("name")
        state_code = states.get("state").get("iso_code")
        return {"state_name": state_name, "state_code": state_code}

    def _get_country_data(self, prestashop, country_id):
        countries = prestashop.get("countries", country_id)
        country_code = countries.get("country").get("iso_code")
        return country_code

    def _get_carrier(self, prestashop, carrier_id):
        carrier_name = False
        try:
            carriers = prestashop.get("carriers", carrier_id)
        except Exception as e:
            _logger.info("Error while getting the shipping data %r",str(e))
        else:
            carrier_name = carriers.get("carrier").get("name")
        return carrier_name

    def _get_currency(self, prestashop, currency_id):
        currency = prestashop.get("currencies", currency_id)
        currency = currency.get("currency").get("iso_code")
        return currency

    def get_order_all(self, prestashop, channel,page_size):
        vals_list = []
        limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
        orders = prestashop.get("orders", options={'limit':limit, 'sort': 'id_ASC'})
        orders = orders.get("orders")
        if isinstance(orders, str):
            return vals_list
        orders = orders.get("order")
        if isinstance(orders,list):
            for order in orders:
                order_id = order.get("attrs").get("id")
                order_vals = self._get_order_by_id(prestashop,channel,order_id)
                if not order_vals:continue
                vals_list.append(order_vals)
        elif isinstance(orders,dict):
            order_id = orders.get("attrs").get("id")
            order_vals = self._get_order_by_id(prestashop,channel,order_id)
            if order_vals:
                vals_list.append(order_vals)
        return vals_list

    def _get_order_by_id(self, prestashop, channel_id, order_id):
        vals = {}
        try :
            order_vals = prestashop.get("orders", order_id)
        except Exception as e:
            _logger.info("Error :- %r",str(e))
            if self.channel_id.debug == "enable":
                raise UserError("Error while getting order:- {}".format(str(e)))
        else:
            order_vals = order_vals.get("order")
            customer_id = order_vals.get("id_customer")
            customer_vals = self._get_customer_name(prestashop,customer_id)
            vals = {
                "name": order_vals.get("reference"),
                'channel': 'prestashop',
                "channel_id": self.channel_id.id,
                "store_id": order_id,
                "partner_id": customer_id,
                "customer_name": customer_vals.get("customer_name"),
                "customer_email": customer_vals.get("customer_email"),
                "payment_method": order_vals.get("payment"),
                "carrier_id": self._get_carrier(prestashop, order_vals.get("id_carrier")),
                "order_state": order_vals.get("current_state"),
                "currency": self._get_currency(prestashop, order_vals.get("id_currency")),
                "date_order": order_vals.get("date_add"),
                "confirmation_date": order_vals.get("delivery_date"),
                "date_invoice": order_vals.get("invoice_date")
            }
            vals.update(self._get_order_line(prestashop,channel_id,order_id))
            invoice_address_id = order_vals.get("id_address_invoice")
            shipping_address_id = order_vals.get("id_address_delivery")
            if not invoice_address_id == shipping_address_id:
                vals["same_shipping_billing"] = False
                vals.update(self._get_shipping_address(prestashop, shipping_address_id,customer_vals))
            invoice_vals = self._get_billing_address(prestashop, invoice_address_id,customer_vals)
            vals.update(invoice_vals)
            vals["customer_phone"] = invoice_vals.get("invoice_phone","")
            vals["customer_mobile"] = invoice_vals.get("invoice_mobile", "")
        return vals

    def _filter_order_using_date(self, prestashop, channel, order_import_date, page_size):
        vals_list = []
        date_created = None
        date = fields.Datetime.to_string(order_import_date)
        limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
        try:
            orders = prestashop.get(
                'orders', options={'filter[date_add]': '>['+date+']', 'date': 1,'limit':limit, 'sort': 'id_ASC'})
            orders = orders.get("orders")
            if isinstance(orders,str):
                return vals_list, date_created
        except Exception as e:
            _logger.info("=====> Error while fetching Orders : %r.", e)
            if self.channel_id.debug == "enable":
                raise UserError("Error while fetching Orders :- {}".format(str(e)))
        else:
            orders = orders.get("order")
            if isinstance(orders, list) and len(orders):
                for order in orders:
                    order_id = order['attrs']['id']
                    vals = self._get_order_by_id(prestashop,channel, order_id)
                    vals_list.append(vals)
                order_id = orders[-1]["attrs"]["id"]
            elif isinstance(orders, dict):
                order_id = orders['attrs']['id']
                vals = self._get_order_by_id(prestashop,channel, order_id)
                vals_list.append(vals)
            last_order = prestashop.get("orders",order_id)
            date_created = last_order.get("order",{}).get("date_add")
        return vals_list, date_created

    def import_now(self, **kwargs):
        data_list = []
        channel = self.channel_id
        prestashop = self._context.get('prestashop')
        page_size = kwargs.get("page_size")
        prestashop_object_id = kwargs.get('prestashop_object_id')
        order_import_date = kwargs.get('prestashop_import_date_from')
        if prestashop_object_id:
            vals = self._get_order_by_id(prestashop, channel,prestashop_object_id)
            data_list.append(vals)
        elif order_import_date:
            data_list, last_added = self._filter_order_using_date(
                prestashop, channel, order_import_date,page_size)
            kwargs["last_added"] = last_added
        else:
            data_list = self.get_order_all(prestashop,channel,page_size)
        return data_list, kwargs