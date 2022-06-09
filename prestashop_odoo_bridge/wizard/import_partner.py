# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from xmlrpc.client import Error
from odoo import api, fields, models, _
from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class ImportPrestashoppartners(models.TransientModel):
    _inherit = 'import.partners'
    _name = "import.prestashop.partners"
    _description = "Import Prestashop Partners"

    def _get_state_data(self, prestashop, state_id):
        vals = {}
        try:
            states = prestashop.get("states", resource_id=state_id)
        except Exception as e:
            _logger.info("error in getting state data... (%r)",str(e))
        else:
            vals["state_name"] = states.get("state").get("name")
            vals["state_code"] = states.get("state").get("iso_code")
        return vals

    def _get_country_data(self, prestashop, country_id):
        country_code = False
        try:
            countries = prestashop.get("countries", resource_id=country_id)
        except Exception as e:
            _logger.info("error in getting country data ... (%r)",str(e))
        else:
            country_code = countries.get("country").get("iso_code")
        return country_code

    def _get_address_by_id(self, prestashop, customer_id):
        vals = {}
        try:
            addresses = prestashop.get(
                "addresses", options={'filter[id_customer]': customer_id})
            addresses = addresses.get('addresses')
            address_list = addresses.get("address")
            if type(address_list) == dict:
                address_id = address_list.get("attrs").get("id")
            elif type(address_list) == list:
                address_id = address_list[0].get("attrs").get("id")
            address = prestashop.get("addresses", address_id)
        except Exception as e:
            _logger.info("error in getting customer address : (%r)",str(e))
        else:
            address = address.get("address")
            state_id = address.get("id_state")
            street = address.get("company") + address.get("address1")
            vals = {
                "street": street,
                "street2": address.get("address2"),
                "zip": address.get("postcode"),
                "city": address.get("city"),
                "country_code": self._get_country_data(prestashop, address.get("id_country"))
            }
            if state_id != "0":
                state_data = self._get_state_data(
                    prestashop, address.get("id_state"))
                vals.update(state_data)
        return vals

    def get_customer_by_id(self, prestashop, customer_id):
        vals = {}
        try:
            customers = prestashop.get("customers", resource_id=customer_id)
        except Exception as e:
            _logger.info("Error:- %r",str(e))
            if self.channel_id.debug == "enable":
                raise UserError("Error while getting Customers :- {}".format(str(e)))
        else:
            customer_vals = customers["customer"]
            store_id = customer_vals.get("id")
            name = customer_vals.get("firstname")
            last_name = customer_vals.get("lastname")
            email = customer_vals.get("email")
            website = customer_vals.get("website")
            vals = {
                "channel_id": self.channel_id.id,
                "channel": 'prestashop',
                "store_id": store_id,
                "name": name,
                "last_name": last_name,
                "email": email,
                "website": website,
            }
            address_vals = self._get_address_by_id(prestashop, customer_id)
            if address_vals:
                vals.update(address_vals)
        return vals

    def filter_customer_using_date(self, prestashop, import_customer_date,page_size):
        vals_list = []
        date_created  = None
        date = fields.Datetime.to_string(import_customer_date)
        limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
        try:
            customers = prestashop.get('customers', options={
                'filter[date_add]': '>['+date+']', 'date': 1,'limit':limit, 'sort': 'id_ASC'})
            customers = customers.get("customers")
            if isinstance(customers,str):
                return vals_list, date_created
        except Exception as e:
            _logger.info("Error while fetching customers : %r.", e)
            if self.channel_id.debug == "enable":
                raise UserError("Error while fetching customers : {}".format(str(e)))
        else:
            customers = customers.get("customer")
            if isinstance(customers, list):
                for customer in customers:
                    customer_id = customer['attrs']['id']
                    vals = self.get_customer_by_id(prestashop, customer_id)
                    if vals:
                        vals_list.append(vals)
                customer_id = customers[-1]["attrs"]["id"]
            elif isinstance(customers, dict):
                customer_id = customers['attrs']['id']
                vals = self.get_customer_by_id(prestashop, customer_id)
                if vals:
                    vals_list.append(vals)
            last_customer = prestashop.get("customers",customer_id)
            date_created = last_customer.get("customer").get("date_add")
        return vals_list, date_created

    def get_customer_all(self, prestashop,page_size):
        vals_list = []
        limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
        try:
            customers = prestashop.get("customers",options={'limit':limit, 'sort': 'id_ASC'})
            customers = customers.get("customers")
            if isinstance(customers,str):
                return vals_list
            customers = customers.get("customer")
        except Exception as e:
            _logger.info("Error in getting Customers => %r",str(e))
            raise UserError("Error in getting Customer {}".format(str(e)))
        else:
            if isinstance(customers,list):
                for customer in customers:
                    customer_id = customer.get("attrs").get("id")
                    customer_vals = self.get_customer_by_id(
                        prestashop, customer_id)
                    if not customer_vals:continue
                    vals_list.append(customer_vals)
            elif isinstance(customers,dict):
                customer_id = customers.get("attrs").get("id")
                customer_vals = self.get_customer_by_id(
                    prestashop, customer_id)
                if customer_vals:
                    vals_list.append(customer_vals)
        return vals_list

    def import_now(self,**kwargs):
        data_list = []
        prestashop = self._context.get('prestashop')
        page_size = kwargs.get("page_size")
        prestashop_object_id = kwargs.get('prestashop_object_id')
        import_customer_date = kwargs.get('prestashop_import_date_from')
        if prestashop_object_id:
            vals = self.get_customer_by_id(prestashop, prestashop_object_id)
            if vals:
                data_list.append(vals)
        elif import_customer_date:
            data_list, last_added = self.filter_customer_using_date(
                prestashop, import_customer_date,page_size)
            kwargs["last_added"] = last_added
        else:
            data_list = self.get_customer_all(prestashop, page_size)
        return data_list, kwargs