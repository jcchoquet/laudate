# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api, fields, models, _
from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError
from odoo.exceptions import  UserError,RedirectWarning, ValidationError ,Warning
from odoo.addons.odoo_multi_channel_sale.tools import extract_list as EL
from odoo.addons.odoo_multi_channel_sale.tools import ensure_string as ES
from odoo.addons.odoo_multi_channel_sale.tools import JoinList as JL
from odoo.addons.odoo_multi_channel_sale.tools import MapId
import logging
_logger = logging.getLogger(__name__)

class ExportProductsPrestashop(models.TransientModel):
    _inherit = ['export.products']

    def action_prestashop_export_product(self):
        active_ids = self._context.get('active_ids')
        prod_env = self.env['product.product']
        temp_ids = [prod_env.browse(
            active_id).product_tmpl_id.id for active_id in active_ids]
        channel_id = self.channel_id.id
        return self.env['export.templates'].create({
            "channel_id": channel_id,
            "operation": "export" if self.operation == "export" else "update",
        }).with_context({
            "active_ids": temp_ids,
            "active_model": "product.template",
        }).action_prestashop_export_template()


class ExportPrestashopProducts(models.TransientModel):
    _inherit = ['export.templates']

    def action_prestashop_export_template(self):
        return self.export_button()

    def prestashop_export_now(self, record):
        res = [False, ""]
        if record.type == "service" :
            return res
        channel_id = self._context.get('channel_id')
        variant_list = []
        prestashop = self._context.get('prestashop')
        try:
            product_bs = prestashop.get('products', options={'schema': 'blank'})
            response = self.prestashop_export_template(
                prestashop, channel_id, product_bs, record)
            _logger.info("response ===========> %r",response)
            if not response[0]:
                return res
            ps_template_id = response[1]
            if record.attribute_line_ids:
                default_variant = record.product_variant_id.id
                for variant_id in record.product_variant_ids:
                    default_attr = "0"
                    if variant_id.id == default_variant:
                        default_attr = "1"
                    response = self.create_combination(
                        prestashop, channel_id, ps_template_id, variant_id,default_attr)
                    if response[0]:
                        variant_list.append(response[1])
                if variant_list:
                    remote_object = CreateRemoteTemplateObject(
                        ps_template_id, variant_list)
                    res = [True, remote_object]
            else:
                product_data = prestashop.get("products",ps_template_id)
                stock_id = product_data.get("product").get(
                    "associations",{}).get("stock_availables",{}).get("stock_available",{}).get("id")
                self.create_normal_product(
                    prestashop, channel_id,record.product_variant_id , ps_template_id,stock_id)
                remote_object = CreateRemoteTemplateObject(
                    ps_template_id, [ps_template_id])
                res = [True, remote_object]
        except Exception as e:
            _logger.info("Error in creating products : %r",str(e))
        # _logger.info("response ===========> %r",response[1])
        return res

    def prestashop_update_now(self, record, remote_id):
        channel_id = self._context.get('channel_id')
        prestashop = self._context.get('prestashop')
        try:
            product_schema = prestashop.get('products', remote_id)
            response = self.prestashop_update_template(
                prestashop, channel_id, product_schema, record, remote_id)
            if not response[0]:
                return [False, ""]
            for product_id in record.product_variant_ids:
                is_mapped = self.env["channel.product.mappings"].search([
                    ("channel_id", "=", channel_id.id),
                    ("product_name.id","=", product_id.id)
                ])
                if is_mapped:
                    res = self.update_combination(prestashop, channel_id, remote_id,is_mapped.store_variant_id, product_id)
                    if res[0]:
                        is_mapped.default_code, is_mapped.barcode = product_id.default_code, product_id.barcode
                else:
                    res = self.create_combination(prestashop,channel_id, remote_id, product_id,"0")
                    if res[0]:
                        vals = {
                            "default_code":product_id.default_code,
                            "barcode":product_id.barcode
                        }
                        channel_id.create_product_mapping(record, product_id,remote_id,res[1],vals)
        except Exception as e:
            _logger.info("Error in updating Product Data : %r", e)
            return [False, ""]
                                                     
                                                                     
                                                   
                                                      
              
                         
                                                                                                                       
                          
                                                                                                           
                 
                                                                                               
                          
                            
                                                               
                                                    
                     
                                                                                               
                                
                                                                    
                                
        return [True,remote_id]

    def _get_store_categ_id(self, prestashop, erp_id):
        mapping_obj = self.env['channel.category.mappings']
        domain = [('odoo_category_id', '=', erp_id.id)]
        check = self.channel_id._match_mapping(
            mapping_obj,
            domain,
            limit=1
        )
        if not check:
            store_category_id = False
            vals = dict(
                channel_id=self.channel_id.id,
                operation='export',
            )
            obj = self.env['export.categories'].create(vals)
            cat_id = obj.with_context({
                "channel_id": self.channel_id,
                "with_product":True,
                "prestashop": prestashop,
            }).prestashop_export_now(erp_id, erp_id.id)
            if cat_id[0]:
                store_category_id = cat_id[1].id
            else:
                _logger.info(
                    "Category cannot be exported to prestashop with id %r", erp_id.id)
            return store_category_id
        return check.store_category_id

    def update_combination(self, prestashop, channel_id, presta_main_product_id,presta_combination_id,product_record):
        try:
            combination_bs = prestashop.get('combinations', presta_combination_id )
            quantity = channel_id.get_quantity(product_record)
            product_price = float(product_record.with_context(pricelist = channel_id.pricelist_name.id).price)
            template_price = float(product_record.product_tmpl_id.with_context(pricelist = channel_id.pricelist_name.id).price)
            price_extra = round(product_price-template_price,2)
            ean13 = product_record.barcode or ''
            default_code = product_record.default_code or ''
            weight = product_record.weight
            combination_bs['combination'].update({
                'ean13': ean13,
                # 'weight': str(weight),
                'reference': default_code,
                'price': str(price_extra),
                'quantity': quantity,
                # 'default_on': default_attr,
                'id_product': str(presta_main_product_id),
                # 'minimal_quantity': '1',
            })
            prestashop.edit('combinations', presta_combination_id, combination_bs)
            if float(quantity) > 0.0:
                self.prestashop_update_quantity(
                    prestashop, presta_main_product_id, quantity, None, presta_combination_id)
        except Exception as e:
            _logger.info('Error in updating Variant(ID: %s).%s' %
                        (str(product_record.id), str(e)))
            if channel_id.debug == "enable":
                raise UserError('Error in updating Variant(ID: %s).%s' % (
                    str(product_record.id), str(e)))
            return [False, ""]
        return [True, int(presta_combination_id)]

    def prestashop_update_template(self, prestashop, channel_id, product_bs, template_record, remote_id):
        cost = template_record.standard_price
        default_code = template_record.default_code or ''
        erp_category_id = template_record.categ_id
        presta_default_categ_id = self._get_store_categ_id(
            prestashop, erp_category_id)
        ps_extra_categ = []
        extra_categories_set = set()
        extra_categories = template_record.channel_category_ids
        extra_categories = extra_categories.filtered(lambda x: x.instance_id.id == channel_id.id)
        if extra_categories:
            for extra_category in extra_categories:
                for categ in extra_category.extra_category_ids:
                    cat_id = self._get_store_categ_id(prestashop, categ)
                    if cat_id not in extra_categories_set:
                        extra_categories_set.add(cat_id)
                        ps_extra_categ.append({'id': str(cat_id)})
                        
        product_bs['product'].update({
             'price': str(round(template_record.with_context(pricelist=channel_id.pricelist_name.id).price, 2)),
            # 'active': '1',
            # 'weight': str(template_record.weight) or '',
            # 'redirect_type': '404',
            # 'minimal_quantity': '1',
            # 'available_for_order': '1',
            'show_price': '1',
            # 'depth': str(template_record.length) or '',
            # 'width': str(template_record.width) or '',
            # 'height': str(template_record.height) or '',
            # 'state': '1',
             'ean13': template_record.barcode or '',
            # 'reference': default_code or '',
            # 'out_of_stock': '2',
            # 'condition': 'new',
            # 'id_category_default': str(presta_default_categ_id)
        })
        # if cost:
            # product_bs['product']['wholesale_price'] = str(round(cost, 3))
        # if type(product_bs['product']['name']['language']) == list:
            # for i in range(len(product_bs['product']['name']['language'])):
                # product_bs['product']['name']['language'][i]['value'] = template_record.name
                # product_bs['product']['link_rewrite']['language'][i]['value'] = channel_id._get_link_rewrite(
                    # '', template_record.name)
                # product_bs['product']['description']['language'][i]['value'] = template_record.description_sale or ""
                # product_bs['product']['description_short']['language'][i]['value'] = template_record.description_purchase or ""
        # else:
            # product_bs['product']['name']['language']['value'] = template_record.name
            # product_bs['product']['link_rewrite']['language']['value'] = channel_id._get_link_rewrite(
                # '', template_record.name)
            # product_bs['product']['description']['language']['value'] = template_record.description_sale or ""
            # product_bs['product']['description_short']['language']['value'] = template_record.description_purchase or ""
        # if 'category' in product_bs['product']['associations']['categories']:
            # product_bs['product']['associations']['categories']['category']['id'] = presta_default_categ_id
        # if 'categories' in product_bs['product']['associations']['categories']:
            # product_bs['product']['associations']['categories']['categories']['id'] = presta_default_categ_id
        # product_bs['product']['associations'].pop(
            # 'combinations', None)
        product_bs['product']['associations'].pop('images', None)
        product_bs['product'].pop('position_in_category', None)
        product_bs['product'].pop('manufacturer_name', None)
        product_bs['product'].pop('quantity', None)
        # if ps_extra_categ:
            # if 'category' in product_bs['product']['associations']['categories']:
                # product_bs['product']['associations']['categories']['category'] = ps_extra_categ
            # if 'categories' in product_bs['product']['associations']['categories']:
                # product_bs['product']['associations']['categories']['categories'] = ps_extra_categ
        
        try:
            prestashop.edit('products', remote_id, product_bs)
        except Exception as e:
            if channel_id.debug == "enable":
                raise UserError( ' Error in updating Product Template(ID: %s).%s' % (str(template_record.id), str(e)))
            return [False, ""]
        return [True, remote_id]

    def prestashop_export_template(self, prestashop, channel_id, product_bs, template_record):
        cost = template_record.standard_price
        default_code = template_record.default_code or ''
        erp_category_id = template_record.categ_id
        presta_default_categ_id = self._get_store_categ_id(
            prestashop, erp_category_id)
        ps_extra_categ = []
        extra_categories_set = set()
        extra_categories = template_record.channel_category_ids
        extra_categories = extra_categories.filtered(lambda x: x.instance_id.id == channel_id.id)
        if extra_categories:
            for extra_category in extra_categories:
                for categ in extra_category.extra_category_ids:
                    cat_id = self._get_store_categ_id(prestashop, categ)
                    if cat_id not in extra_categories_set:
                        extra_categories_set.add(cat_id)
                        ps_extra_categ.append({'id': str(cat_id)})

        product_bs['product'].update({
            'price': str(round(template_record.with_context(pricelist=channel_id.pricelist_name.id).price, 2)),
            'active': '1',
            # 'weight': str(template_record.weight) or '',
            'redirect_type': '404',
            'minimal_quantity': '1',
            'available_for_order': '1',
            'show_price': '1',
            'depth': str(template_record.length) or '',
            'width': str(template_record.width) or '',
            'height': str(template_record.height) or '',
            'state': '1',
            'ean13': template_record.barcode or '',
            'reference': default_code or '',
            'out_of_stock': '2',
            'condition': 'new',
            'id_category_default': str(presta_default_categ_id)
        })
        if cost:
            product_bs['product']['wholesale_price'] = str(round(cost, 3))
        if type(product_bs['product']['name']['language']) == list:
            for i in range(len(product_bs['product']['name']['language'])):
                product_bs['product']['name']['language'][i]['value'] = template_record.name
                product_bs['product']['link_rewrite']['language'][i]['value'] = channel_id._get_link_rewrite(
                    '', template_record.name)
                product_bs['product']['description']['language'][i]['value'] = template_record.description_sale or ""
                product_bs['product']['description_short']['language'][i]['value'] = template_record.description_purchase or ""
        else:
            product_bs['product']['name']['language']['value'] = template_record.name
            product_bs['product']['link_rewrite']['language']['value'] = channel_id._get_link_rewrite(
                '', template_record.name)
            product_bs['product']['description']['language']['value'] = template_record.description_sale or ""
            product_bs['product']['description_short']['language']['value'] = template_record.description_purchase or ""
        if 'category' in product_bs['product']['associations']['categories']:
            product_bs['product']['associations']['categories']['category']['id'] = str(
                presta_default_categ_id)
        if 'categories' in product_bs['product']['associations']['categories']:
            product_bs['product']['associations']['categories']['categories']['id'] = str(
                presta_default_categ_id)
        product_bs['product']['associations'].pop(
            'combinations', None)
        product_bs['product']['associations'].pop('images', None)
        product_bs['product'].pop('position_in_category', None)
        # product_bs['product'].pop('manufacturer_name', None)

        if ps_extra_categ:
            if 'category' in product_bs['product']['associations']['categories']:
                product_bs['product']['associations']['categories']['category'] = ps_extra_categ
            if 'categories' in product_bs['product']['associations']['categories']:
                product_bs['product']['associations']['categories']['categories'] = ps_extra_categ
        try:
            returnid = prestashop.add('products', product_bs)
        except Exception as e:
            _logger.info("Error in creating Product Template(ID: %s).%s" %
                         (str(presta_default_categ_id), str(e)))
            if channel_id.debug == "enable":
                raise UserError("Error in creating Product Template(ID: %s).%s" %
                         (str(presta_default_categ_id), str(e)))
            return [False, ""]
        return [True, returnid]

    def create_combination(
        self, prestashop, channel_id, presta_main_product_id,product_record, default_attr):
        presta_dim_list = []
        attribute_value_ids = product_record.product_template_attribute_value_ids
        if attribute_value_ids:
            res = self.env['export.prestashop.attribute'].create({
                "channel_id": channel_id.id,
                "operation": "export",
            })
            for attribute_value_id in attribute_value_ids:
                attribute_value_id = attribute_value_id.product_attribute_value_id
                store_value_id = res.with_context({
                    "channel_id": channel_id,
                    "prestashop": prestashop,
                }).export_now(attribute_value_id)
                if store_value_id:
                    presta_dim_list.append({"id": store_value_id})

        try:
            combination_bs = prestashop.get('combinations', options={'schema': 'blank'})
                                                   
            image_id = False
            quantity = channel_id.get_quantity(product_record)
            image = product_record.image_1920
            if image:
                image_id = self.create_images(
                    prestashop, image, presta_main_product_id)
            product_price = float(product_record.with_context(pricelist = channel_id.pricelist_name.id).price)
            template_price = float(product_record.product_tmpl_id.with_context(pricelist = channel_id.pricelist_name.id).price)
            price_extra = round(product_price - template_price,2)
            ean13 = product_record.barcode or ''
            default_code = product_record.default_code or ''
            weight = product_record.weight or ""
            if presta_dim_list:
                combination_bs['combination']['associations']['product_option_values']['product_option_values'] = presta_dim_list
                combination_bs['combination'].update({
                    'ean13': ean13,
                    'weight': str(weight),
                    'reference': default_code,
                    'price': str(price_extra),
                    'quantity': quantity,
                    'default_on': default_attr,
                    'id_product': str(presta_main_product_id),
                    'minimal_quantity': '1',
                })
                returnid = prestashop.add('combinations', combination_bs)
                data = prestashop.get('combinations',returnid)
                if image_id:
                    data["combination"]["associations"]["images"]["image"] = {'id': str(image_id)}
                prestashop.edit('combinations', returnid, data)
                if default_attr:
                    temp_data = prestashop.get('products', presta_main_product_id)
                    temp_data['product']['id_default_combination'] = returnid
                    temp_data['product'].pop('position_in_category', None)
                    temp_data['product'].pop('manufacturer_name', None)
                    temp_data['product'].pop('quantity', None)
                    temp_data['product'].pop('type', None)
                    prestashop.edit('products', presta_main_product_id, temp_data)
                pid = int(returnid)
                if float(quantity) > 0.0:
                    self.prestashop_update_quantity(
                        prestashop, presta_main_product_id, quantity, None, pid)
                
        except Exception as e:
            _logger.info('Error in creating Variant(ID: %s).%s' %
                        (str(product_record.id), str(e)))
            if channel_id.debug == "enable":
                raise UserError('Error in creating Variant(ID: %s).%s' % (
                    str(product_record.id), str(e)))
            return [False, ""]
        return [True, pid]

    def create_normal_product(
        self, prestashop, channel_id,product_record, prest_main_product_id, stock_id):
        erp_category_id = product_record.categ_id
        default_code = product_record.default_code or ''
        presta_default_categ_id = self._get_store_categ_id(prestashop,erp_category_id)
        try:
            add_data = prestashop.get('products', prest_main_product_id)
            add_data['product'].update({
                'price': str(round(product_record.with_context(pricelist=channel_id.pricelist_name.id).price, 2)),
                'active': '1',
                'redirect_type': '404',
                'minimal_quantity': '1',
                'available_for_order': '1',
                'show_price': '1',
                'state':'1',
                'out_of_stock': '2',
                'default_on': '1',
                'condition': 'new',
                'reference': default_code,
                'id_category_default': presta_default_categ_id
            })
            add_data['product'].pop('position_in_category', None)
            add_data['product'].pop('manufacturer_name', None)
            add_data['product'].pop('quantity', None)
            add_data['product'].pop('type', None)
            prestashop.edit('products', prest_main_product_id, add_data)
            if product_record.image_1920:
                self.create_images(
                    prestashop, product_record.image_1920, prest_main_product_id)
            quantity = channel_id.get_quantity(product_record)
            if float(quantity) > 0.0:
                self.prestashop_update_quantity(
                    prestashop, prest_main_product_id, quantity, stock_id)
        except Exception as e:
            _logger.info("Error in Creating Simple Product: %r", str(e))
            return [False, ""]
        return [True, prest_main_product_id]

    @api.model
    def create_images(self, prestashop, image_data, resource_id, image_name=None, resource='images/products'):
        if image_name == None:
            image_name = 'op' + str(resource_id) + '.png'
        try:
            returnid = prestashop.add(
                str(resource) + '/' + str(resource_id), image_data, image_name)
        except Exception as e:
            _logger.info("Error in Creating Images : %r",str(e))
            return False
        return returnid

    def prestashop_update_quantity(self, prestashop, pid, quantity, stock_id=None, attribute_id=None):
        try:
            if stock_id:
                stock_data = prestashop.get('stock_availables', stock_id)
                if stock_data.get("stock_available"):
                    stock_data['stock_available']['quantity'] = quantity
                prestashop.edit('stock_availables', stock_id, stock_data)
            elif attribute_id:
                stock_search = prestashop.get('stock_availables',
                    options={'filter[id_product]': pid, 'filter[id_product_attribute]': attribute_id})
                if type(stock_search.get("stock_availables",False)) == dict:
                    stock_id = stock_search['stock_availables']['stock_available']['attrs']['id']
                    stock_data = prestashop.get('stock_availables', stock_id)
                    stock_data['stock_available']['quantity'] = quantity
                    prestashop.edit('stock_availables', stock_id, stock_data)
            else:
                    product_data = prestashop.get('products', pid)
                    product_data = product_data.get("product")
                    stock_available = product_data.get("associations",{}).get("stock_availables")
                    if stock_available:
                        stock_id = stock_available.get("stock_available").get("id")
                        stock_data = prestashop.get('stock_availables', stock_id)
                        if stock_data.get("stock_available"):
                            stock_data['stock_available']['quantity'] = quantity
                        prestashop.edit('stock_availables', stock_id, stock_data)
        except Exception as e:
            _logger.info("Error in updating stock quantity : %r",str(e))
            return False
        return True

class CreateRemoteTemplateObject:

    def __init__(self, product_template_id, product_variant_list):
        self.id = product_template_id
        self.variants = (CreateRemoteVariantObject(product_variant_id)
                         for product_variant_id in product_variant_list)


class CreateRemoteVariantObject:

    def __init__(self, product_variant_id):
        self.id = product_variant_id
