#!/usr/bin/env python
# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api, fields, models, _
from odoo import tools
from .prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError
from odoo.addons.odoo_multi_channel_sale.tools import extract_list as EL
from odoo.addons.odoo_multi_channel_sale.tools import  _unescape

from odoo.exceptions import UserError
import re
import base64
import itertools
import logging
_logger     = logging.getLogger(__name__)


Type = [
    ('simple','Simple Product'),
    ('downloadable','Downloadable Product'),
    ('grouped','Grouped Product'),
    ('virtual','Virtual Product'),
    ('bundle','Bundle Product'),
]
TaxType = [
    ('include','Include In Price'),
    ('exclude','Exclude In Price')
]
Boolean = [
    ('1', 'True'),
    ('0', 'False'),
]


class MultiChannelSale(models.Model):
    _inherit = "multi.channel.sale"

    prestashop_base_uri = fields.Char(
        string = 'Base URI'
    )
    prestashop_api_key = fields.Char(
        string = 'API Key'
    )
    ps_language_id = fields.Char(
        'Prestashop Language Id',
        size = 2,
        help="Prestashop's Default language Id "
    )

    default_tax_type = fields.Selection(
        selection = TaxType,
        string = 'Default Tax Type',
        default = 'exclude',
        required = 1
    )
    ps_default_product_type = fields.Selection(
        selection = Type,
        string = 'Default Product Type',
        default = 'simple',
        required = 1,
    )
    ps_default_tax_rule_id = fields.Char(
        string = 'Default Tax Class ID',
        default = '0',
        required = 1,
    )
    export_order_shipment = fields.Selection(
        selection = Boolean,
        string = 'Export  Order Shipment Over Prestashop',
        default = '1',
        required = 1,
    )
    export_order_invoice = fields.Selection(
        selection = Boolean,
        string = 'Export  Order Invoice Over Prestashop',
        default = '1',
        required = 1,
    )

    @api.model
    def get_channel(self):
        result = super(MultiChannelSale, self).get_channel()
        result.append(("prestashop", "Prestashop"))
        return result

    def get_core_feature_compatible_channels(self):
        vals = super().get_core_feature_compatible_channels()
        vals.append('prestashop')
        return vals

    def connect_prestashop(self):
        message = '<br/> Credentials successfully validated.'
        state = 'validate'
        try:
            prestashop = PrestaShopWebServiceDict(
                self.prestashop_base_uri, self.prestashop_api_key)
            if prestashop:
                languages = prestashop.get("languages", options = {'filter[active]':'1'})
                if languages.get("languages",{}).get("language"):
                    message = '<br/> Credentials successfully validated.'
        except Exception as e:
            message = 'Connection Error: '+str(e)+'\r\n'
            state = 'error'
            return False,message
        return True, message

    def sync_order_feeds(self, vals, **kwargs):
        for line_id in vals[0]['line_ids']:
            line_id = line_id[2]
            if line_id['line_source'] == "discount":
                line_price = line_id['line_price_unit']
                line_id['line_price_unit'] = line_price['total_discounts_tax_incl'] if self.default_tax_type == 'include'\
                    else line_price['total_discounts_tax_excl']
        res = super().sync_order_feeds(vals, **kwargs)
        return res

    def import_prestashop(self, object, **kwargs):
        prestashop = PrestaShopWebServiceDict(
            self.prestashop_base_uri, self.prestashop_api_key)
        data_list = []
        if prestashop:
            if object == 'product.category':
                data_list, kwargs = self.import_prestashop_categories(
                    prestashop, **kwargs)
            elif object == 'res.partner':
                data_list, kwargs = self.import_prestashop_customers(
                    prestashop, **kwargs)
            elif object == 'product.template':
                data_list ,kwargs= self.import_prestashop_products(
                    prestashop, **kwargs)
            elif object == 'sale.order':
                data_list, kwargs = self.import_prestashop_orders(prestashop, **kwargs)
            elif object == "delivery.carrier":
                data_list,kwargs = self.import_prestashop_shippings(prestashop, **kwargs)
            return data_list, kwargs

    def import_prestashop_products(self, prestashop, **kwargs):
        vals = dict(
            channel_id=self.id,
            operation='import',
        )
        obj = self.env['import.prestashop.products'].create(vals)
        return obj.with_context({
            "prestashop": prestashop,
        }).import_now(**kwargs)

    def import_prestashop_categories(self, prestashop, **kwargs):
        vals = dict(
            channel_id=self.id,
            operation='import',
        )
        obj = self.env['import.prestashop.categories'].create(vals)
        return obj.with_context({
            "prestashop": prestashop,
        }).import_now(**kwargs)

    def import_prestashop_customers(self, prestashop, **kwargs):
        vals = dict(
            channel_id=self.id,
            operation='import',
        )
        obj = self.env['import.prestashop.partners'].create(vals)
        return obj.with_context({
            "prestashop": prestashop,
        }).import_now(**kwargs)

    def import_prestashop_shippings(self, prestashop, **kwargs):
        vals = dict(
            channel_id=self.id,
            operation='import',
        )
        obj = self.env['import.prestashop.shipping'].create(vals)
        return obj.with_context({
            "prestashop": prestashop,
        }).import_now(**kwargs)

    def import_prestashop_orders(self, prestashop, **kwargs):
        vals = dict(
            channel_id=self.id,
            operation='import',
        )
        obj = self.env['import.prestashop.orders'].create(vals)
        return obj.with_context({
            'prestashop': prestashop,
        }).import_now(**kwargs)

    def export_prestashop(self, record):
        prestashop = PrestaShopWebServiceDict(
            self.prestashop_base_uri, self.prestashop_api_key)
        data_list = []
        if prestashop:
            if record._name == 'product.category':
                initial_record_id = record.id
                data_list = self.export_prestashop_categories(
                    prestashop, record, initial_record_id)
            elif record._name == 'product.template':
                data_list = self.export_prestashop_products(prestashop, record)
            return data_list

    def export_prestashop_products(self, prestashop, record):
        vals = dict(
            channel_id=self.id,
            operation='export',
        )
        obj = self.env['export.templates'].create(vals)
        return obj.with_context({
            'prestashop': prestashop,
            'channel_id': self,
        }).prestashop_export_now(record)

    def export_prestashop_categories(self, prestashop, record, initial_record_id):
        vals = dict(
            channel_id=self.id,
            operation='export',
        )
        obj = self.env['export.categories'].create(vals)
        return obj.with_context({
            'prestashop': prestashop,
            'channel_id': self,
        }).prestashop_export_now(record, initial_record_id)

    def update_prestashop(self, record, get_remote_id):
        prestashop = PrestaShopWebServiceDict(
            self.prestashop_base_uri, self.prestashop_api_key)
        data_list = []
        if prestashop:
            remote_id = get_remote_id(record)
            if record._name == 'product.category':
                initial_record_id  = record.id
                data_list = self.update_prestashop_categories(prestashop, record, initial_record_id,remote_id)
            if record._name == 'product.template':
                data_list = self.update_prestashop_products(
                    prestashop, record, remote_id)
            return data_list

    def update_prestashop_categories(self,prestashop, record, initial_record_id,remote_id):
        vals = dict(
            channel_id=self.id,
            operation='update',
        )
        obj = self.env['export.categories'].create(vals)
        return obj.with_context({
            'prestashop': prestashop,
            'channel_id': self,
        }).prestashop_update_now(record, remote_id)

    def update_prestashop_products(self, prestashop, record, remote_id):
        vals = dict(
            channel_id=self.id,
            operation='update',
        )
        obj = self.env['export.templates'].create(vals)
        return obj.with_context({
            'prestashop': prestashop,
            'channel_id': self,
        }).prestashop_update_now(record, remote_id)

    def prestashop_import_order_cron(self):
        kw = dict(
            object="sale.order",
            prestashop_import_date_from=self.import_order_date
        )
        _logger.info("~~~~~~~~ Import Prestashop Order Cron Started~~~~~~~~~~")
        self.env["import.operation"].create({
            "channel_id":self.id
        }).prestashop_import_with_filter(**kw)
        return True

    def prestashop_import_product_cron(self):
        kw = dict(
            object="product.template",
            prestashop_import_date_from=self.import_product_date
        )
        _logger.info("~~~~~~~~ Import Prestashop Product Cron Started~~~~~~~~~~")

        self.env["import.operation"].create({
            "channel_id":self.id
        }).prestashop_import_with_filter(**kw)
        return True

    def prestashop_import_partner_cron(self):
        kw = dict(
            object="res.partner",
            prestashop_import_date_from=self.import_customer_date
        )
        _logger.info("~~~~~~~~ Import Prestashop Partner Cron Started~~~~~~~~~~")
        self.env["import.operation"].create({
            "channel_id":self.id
        }).prestashop_import_with_filter(**kw)
        return True

    def prestashop_import_category_cron(self):
        kw = dict(
            object="product.category",
        )
        _logger.info("~~~~~~~~ Import Prestashop Category Cron Started~~~~~~~~~~")

        self.env["import.operation"].create({
            "channel_id":self.id
        }).prestashop_import_with_filter(**kw)
        return True

    def sync_quantity_prestashop(self, mapping, qty):
        prestashop = PrestaShopWebServiceDict(
            self.prestashop_base_uri, self.prestashop_api_key)
        if self.auto_sync_stock:
            pres_combination_id = mapping.store_variant_id
            pres_product_id = mapping.store_product_id
            if pres_product_id == pres_combination_id:
                self.env['export.templates'].prestashop_update_quantity(prestashop,pres_product_id , qty)
            else:
                self.env['export.templates'].prestashop_update_quantity(prestashop,pres_product_id , qty,attribute_id = pres_combination_id)
            return True

    @api.model
    def _prestashop_get_product_images_vals(self, media):
        vals = dict()
        message = ''
        data = None
        image_url = media
        if image_url:
            prestashop = self._context['prestashop']
            try:
                data = prestashop.get(image_url)
                image_data = base64.b64encode(data)
            except Exception as e:
                message += '<br/>%s'%(e)
            else:
                vals['image'] = image_data
                return vals
        return {'image':False}

    def _get_link_rewrite(self, zip, string):
        if type(string) != str:
            string = string.encode('ascii','ignore')
            string = str(string)
        string = re.sub('[^A-Za-z0-9]+',' ',string)
        string = string.replace(' ', '-').replace('/', '-')
        string = string.lower()
        return string
