# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
from xmlrpc.client import Error
import logging
from odoo.exceptions import  UserError,RedirectWarning, ValidationError
from odoo import api, fields, models, _
from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError
try:
    from odoo.loglevels import ustr as pob_decode
except:
    from odoo.tools.misc import ustr as pob_decode
_logger = logging.getLogger(__name__)


class ImportPrestashopCategories(models.TransientModel):
    _inherit = ['import.categories']
    _name = "import.prestashop.categories"
    _description = "Import Prestashop Categories"

    def get_category_all(self, prestashop,page_size):
        if prestashop:
            vals_list = []
            limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
            categories = prestashop.get("categories", options={
                                        'display': '[is_root_category,id_parent,id,name]','limit':limit})
            categories = categories.get("categories")
            if isinstance(categories,str):
                return vals_list
            categories = categories.get("category")
            if isinstance(categories, list):
                for category in categories:
                    is_root_category = category.get("is_root_category")
                    id_parent = category.get("id_parent")
                    store_id = category.get("id")
                    vals = {
                        "channel_id": self.channel_id.id,
                        "channel": 'prestashop',
                        "leaf_category": is_root_category,
                        "store_id": store_id,
                    }
                    if type(category['name']['language'])==list:
                        channel_lang = self.channel_id.ps_language_id
                        for cat_name in category['name']['language']:
                            if cat_name['attrs']['id'] == channel_lang:
                                vals["name"] = cat_name['value']
                    else:
                        vals['name'] = category.get('name')['language']['value']
                    if id_parent != '0':
                        vals['parent_id'] = id_parent
                    vals_list.append(vals)
            elif isinstance(categories, dict):
                is_root_category = categories.get("is_root_category")
                id_parent = categories.get("id_parent")
                store_id = categories.get("id")
                vals = {
                    "channel_id": self.channel_id.id,
                    "channel": 'prestashop',
                    "leaf_category": is_root_category,
                    "store_id": store_id,
                }
                if type(categories['name']['language'])==list:
                    channel_lang = self.channel_id.ps_language_id
                    for cat_name in categories['name']['language']:
                        if cat_name['attrs']['id'] == channel_lang:
                            vals["name"] = cat_name['value']
                else:
                    vals['name'] = categories.get('name')['language']['value']
                if id_parent != '0':
                    vals['parent_id'] = id_parent
                vals_list.append(vals)
            return vals_list

    def filter_category_using_date(self, prestashop, import_category_date,page_size):
        if prestashop:
            vals_list = []
            date = fields.Datetime.to_string(import_category_date)
            limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
            try:
                categories = prestashop.get('categories', options={
                    'filter[date_add]': '>['+date+']', 'date': 1,'limit':limit})
                categories = categories.get("categories")
                if isinstance(categories,str):
                    return vals_list
            except Exception as e:
                _logger.info("=====> Error while fetching categories : %r.", e)
                if self.channel_id.debug == "enable":
                    raise UserError("Error while fetching categories : %r.", e)
            else:
                categories = categories.get('category')
                if isinstance(categories, list) and categories:
                    for category in categories:
                        category_id = category['attrs']['id']
                        vals = self.get_category_by_id(prestashop, category_id)
                        if vals:
                            vals_list.append(vals)
                elif isinstance(categories, dict):
                    category_id = categories['attrs']['id']
                    vals = self.get_category_by_id(prestashop, category_id)
                    if vals:
                        vals_list.append(vals)
            return vals_list

    def get_category_by_id(self, prestashop, category_id):
        if prestashop:
            vals = {}
            try:
                categories = prestashop.get("categories", resource_id=category_id)
            except Exception as e:
                _logger.info("Error :- %r",str(e))
                if self.channel_id.debug == "enable":
                    raise UserError("Error while getting categories .....")
                return vals
            else:
                categories = categories.get("category")
                is_root_category = categories.get("is_root_category")
                id_parent = categories.get("id_parent")
                id_shop_default = categories.get("id")
                if type(categories['name']['language'])==list:
                    for cat_name in categories['name']['language']:
                        if cat_name['attrs']['id'] == self.channel_id.ps_language_id:
                            name = cat_name['value']
                else:
                    name = categories.get('name')['language']['value']
                vals = {
                        "channel_id": self.channel_id.id,
                        "channel": 'prestashop',
                        "leaf_category": is_root_category,
                        "store_id": id_shop_default,
                        "name": name
                    }
                if id_parent != "0":
                    vals['parent_id'] = id_parent
                return vals

    def import_now(self,**kwargs):
        data_list = []
        page_size = kwargs.get("page_size")
        prestashop = self._context.get('prestashop')
        prestashop_object_id = kwargs.get('prestashop_object_id')
        import_category_date = self._context.get("prestashop_import_date_from")
        if prestashop_object_id:
            vals = self.get_category_by_id(prestashop, prestashop_object_id)
            if vals:
                data_list.append(vals)
        elif import_category_date:
            data_list = self.filter_category_using_date(
                prestashop, import_category_date,page_size)
        else:
            data_list = self.get_category_all(prestashop,page_size)
        return data_list,kwargs