# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#############H##########Y###########P##########N###########O##########S########
from xmlrpc.client import Error
import itertools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo import api, fields, models, _
from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService, PrestaShopWebServiceDict, PrestaShopWebServiceError, PrestaShopAuthenticationError

import logging
_logger = logging.getLogger(__name__)

class ExportPrestashopCategories(models.TransientModel):
    _inherit = 'export.categories'

    def action_prestashop_export_category(self):
        return self.export_button()

    def action_prestashop_update_category(self):
        return self.update_button()

    def prestashop_create_category(self, prestashop, channel, record, initial_record_id, p_cat_id,
                meta_description='', meta_keywords='', with_product = False):
        cat_name = record.name
        cat_data = None
        try:
            cat_data = prestashop.get(
                'categories', options={'schema': 'blank'})
        except Exception as e:
            _logger.info("Error in getting Blank Category Schema : %r",str(e))
        else:
            if type(cat_data['category']['name']['language']) == list:
                for i in range(len(cat_data['category']['name']['language'])):
                    cat_data['category']['name']['language'][i]['value'] = cat_name
                    cat_data['category']['link_rewrite']['language'][i]['value'] = channel._get_link_rewrite(
                        zip, cat_name)
                    # cat_data['category']['description']['language'][i]['value'] = record.description
                    cat_data['category']['meta_description']['language'][i]['value'] = meta_description
                    cat_data['category']['meta_keywords']['language'][i]['value'] = meta_keywords
                    cat_data['category']['meta_title']['language'][i]['value'] = record.name
            else:
                cat_data['category']['name']['language']['value'] = cat_name
                cat_data['category']['link_rewrite']['language']['value'] = channel._get_link_rewrite(
                    zip, cat_name)
                # cat_data['category']['description']['language']['value'] = record.description
                cat_data['category']['meta_description']['language']['value'] = meta_description
                cat_data['category']['meta_keywords']['language']['value'] = meta_keywords
                cat_data['category']['meta_title']['language']['value'] = record.name
            cat_data['category']['is_root_category'] = '0'
            cat_data['category']['id_parent'] = p_cat_id
            cat_data['category']['active'] = '1'
            try:
                returnid = prestashop.add('categories', cat_data)
            except Exception as e:
                _logger.info('Category Data Not Exported::::::::::::: %r ::::::::::::::::', [
                             str(e), record.id, cat_data])
                if channel.debug == "enable":
                    raise UserError('Category Data Not Exported :- {} '.format(str(e)))
            else:
                if record.id !=initial_record_id or with_product:
                    channel.create_category_mapping(record, returnid)
                return returnid

    def prestashop_export_now(self, record, initial_record_id):
        result_list = [False, ""]
        with_product = self._context.get('with_product')
        channel = self._context.get('channel_id')
        prestashop = self._context.get('prestashop')
        cat_id = self.prestashop_sync_category(
            channel, prestashop, record, initial_record_id, with_product)
        if cat_id:
            remote_object = CreateRemoteObject(cat_id)
            result_list = [True, remote_object]
        return result_list

    def prestashop_sync_category(self, channel, prestashop, record, initial_record_id, with_product):
        p_cat_id = 2
        res = ""
        parent_id = record.parent_id
        if parent_id.id:
            is_parent_mapped = self.env["channel.category.mappings"].search([
                ("channel_id","=",channel.id),
                ("odoo_category_id","=",parent_id.id),
            ])
            if not is_parent_mapped:
                p_cat_id = self.with_context({
                    'with_product': with_product,
                    "channel_id": channel,
                    "prestashop": prestashop,
                }).prestashop_export_now(record.parent_id, initial_record_id)
                if p_cat_id[0]:
                    p_cat_id = p_cat_id[1].id
            else:
                p_cat_id = is_parent_mapped.store_category_id
        res = self.prestashop_create_category(
            prestashop, channel, record, initial_record_id, p_cat_id,with_product = with_product)
        return res

    def prestashop_update_now(self,record,remote_id):
        result_list = [False, ""]
        channel = self._context.get('channel_id')
        prestashop = self._context.get('prestashop')
        cat_id = self.sync_mapped_category(
            channel, prestashop, record, remote_id)
        if cat_id:
            result_list = [True, cat_id]
        return result_list

    def sync_mapped_category(self,channel,prestashop,record,remote_id):
        p_cat_id = 2
        res = ""
        parent_id = record.parent_id
        if parent_id.id:
            is_mapped = self.env["channel.category.mappings"].search([
                ("channel_id","=",channel.id),
                ("odoo_category_id","=",parent_id.id)
                ])
            if is_mapped:
                store_category_id = int(is_mapped.store_category_id)
                p_cat_id = self.with_context({
                    "prestashop":prestashop,
                    "channel_id":channel,
                }).prestashop_update_now(parent_id,store_category_id)
                if p_cat_id[0] :
                    p_cat_id =p_cat_id[1]
            else:
                p_cat_id = self.with_context({
                    "prestashop":prestashop,
                    "channel_id":channel,
                }).prestashop_export_now(parent_id,parent_id.id)
                if p_cat_id[0]:
                    p_cat_id = p_cat_id[1].id
                    channel.create_category_mapping(parent_id, p_cat_id)
        res = self._update_category(
            prestashop, channel, record, p_cat_id,remote_id)
        return res

    def _update_category(self, prestashop, channel, record, p_cat_id,remote_id):
        cat_id = record.id
        cat_name = record.name
        cat_data = None
        try:
            cat_data = prestashop.get('categories',remote_id)
        except Exception as e:
            _logger.info("Category Id:%s ;Error in getting schema for categories.Detail : %s" %(cat_id,str(e)))
        else:
            cat_data["category"].pop("level_depth")
            cat_data["category"].pop("nb_products_recursive")
            if type(cat_data['category']['name']['language']) == list:
                for i in range(len(cat_data['category']['name']['language'])):
                    cat_data['category']['name']['language'][i]['value'] = cat_name
                    cat_data['category']['link_rewrite']['language'][i]['value'] = channel._get_link_rewrite(
                        zip, cat_name)
                    # cat_data['category']['description']['language'][i]['value'] = record.description
            else:
                cat_data['category']['name']['language']['value'] = cat_name
                cat_data['category']['link_rewrite']['language']['value'] = channel._get_link_rewrite(
                    zip, cat_name)
                cat_data['category']['meta_title']['language']['value'] = record.name
            cat_data['category']['id_parent'] = p_cat_id
            cat_data['category']['active'] = '1'
            try:
                returnid = prestashop.edit('categories', remote_id, cat_data)
            except Exception as e:
                _logger.info('Category Data Not updated::::::::::::: %r ::::::::::::::::', [
                             str(e), record.id, cat_data])
                if self.channel_id.debug == "enable":
                    raise UserError('Category Data Not updated :- {}'.format(str(e)))
            else:
                return remote_id

class CreateRemoteObject:

    def __init__(self, id):
        self.id = id
