# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################
import logging
import itertools
import binascii
from xmlrpc.client import Error
from odoo import api, fields, models, _
from odoo.addons.odoo_multi_channel_sale.tools import MapId
from odoo.exceptions import  UserError,RedirectWarning, ValidationError
from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService,PrestaShopWebServiceDict,PrestaShopWebServiceError,PrestaShopAuthenticationError
try:
    import html2text
except Exception as e:
    pass

_logger = logging.getLogger(__name__)

OdooType = [
    ('simple','product'),
    ('downloadable','service'),#digital
    ('grouped','service'),
    ('virtual','service'),
    ('bundle','service'),
]

CHANNELDOMAIN = [
    ('channel', '=', 'prestashop'),
    ('state', '=', 'validate')
]

class ImportPrestashopProducts(models.TransientModel):
    _inherit = 'import.templates'
    _name = "import.prestashop.products"
    _description = "Import Prestashop Products"

    def _get_default_image(self, prestashop, product_id, default_image_id):
        if prestashop:
            image_data = 'images/products/%s/%s'%(product_id, default_image_id)
            image_data = self.channel_id.with_context({
                "prestashop":prestashop
            })._prestashop_get_product_images_vals(image_data)
            image_data = image_data.get("image")
            if not image_data:
                return False
            return image_data

    def _get_product_basics(self, prestashop, products):
        if prestashop:
            if type(products['name']['language'])==list:
                for prod_name in products['name']['language']:
                    if prod_name['attrs']['id'] == self.channel_id.ps_language_id:
                        name = prod_name['value']
            else:
                name = products.get('name')['language']['value']
            store_id = products.get("id")
            default_code = products.get("reference","")
            default_image_id = products.get("id_default_image",{}).get('value')
            list_price = products.get("price","")
            standard_price = products.get("wholesale_price","")
            categ_ids = products.get("associations").get("categories").get("category")
            extra_categ_ids = ''
            category_ids = []
            if categ_ids:
                if type(categ_ids)==list:
                    for categ_id in categ_ids:
                        self.create_category_feed(prestashop,self.channel_id,categ_id["id"])
                        category_ids.append(categ_id["id"])
                else:
                    self.create_category_feed(prestashop,self.channel_id,categ_ids["id"])
                    category_ids.append(categ_ids["id"])
                extra_categ_ids = ','.join(category_ids)

            length = products.get("depth","")
            width = products.get("width","")
            height = products.get("height","")
            # weight = products.get("weight","")
        if type(products['description']['language'])==list:
            for pro_name in products['description']['language']:
                if pro_name['attrs']['id'] ==self. channel_id.ps_language_id:
                    try:
                        description_sale = html2text.html2text(pro_name['value'])
                    except:
                        description_sale = pro_name['value']
        else:
            try:
                description_sale = html2text.html2text(products.get('description')['language']['value'])
            except:
                description_sale = products.get('description')['language']['value']

            if type(products['description_short']['language'])==list:
                for pro_name in products['description_short']['language']:
                    if pro_name['attrs']['id'] == self.channel_id.ps_language_id:
                        try:
                            description_purchase = html2text.html2text(pro_name['value'])
                        except:
                            description_purchase = pro_name['value']
            else:
                try:
                    description_purchase = html2text.html2text(products.get('description_short')['language']['value'])
                except:
                    description_purchase = products.get('description_short')['language']['value']
            wk_product_id_type = products.get("ean13")
            barcode = products.get("ean13")
            vals = dict(
                        name = name,
                        channel_id = self.channel_id.id,
                        channel = 'prestashop',
                        store_id = store_id,
                        list_price = list_price,
                        standard_price = standard_price,
                        default_code = default_code,
                        # type = product_type,
                        extra_categ_ids = extra_categ_ids,
                        length = length,
                        width = width,
                        height = height,
                        # weight = weight,
                        description_sale = description_sale,
                        description_purchase = description_purchase,
                        wk_product_id_type = wk_product_id_type,
                        barcode = barcode,
                        #hs_code = hs_code,
                    )
            stock_available = products.get("associations",{}).get("stock_availables",{}).get("stock_available",{})
            if isinstance(stock_available, dict):
                stock_id = stock_available.get("id")
            elif isinstance(stock_available, list):
                stock_id = stock_available[0].get("id")
            if stock_id:
                stock_data = False
                try:
                    stock_data = prestashop.get("stock_availables", stock_id)
                except:
                    _logger.info("error in getting stock data .....")
                else:
                    if stock_data:
                        vals["qty_available"] = stock_data["stock_available"].get("quantity")
            if products.get("associations").get("images",{}).get("image") and type(default_image_id) == str:
                image = self._get_default_image(prestashop, products['id'], default_image_id)
                vals['image'] = image
            return vals

    def create_category_feed(self,prestashop,channel_id,categ_id):
        is_feed = self.env["category.feed"].search([
            ("channel_id","=",channel_id.id),
            ("store_id","=",categ_id)
            ])
        if not is_feed:
            categ_data = self.env["import.prestashop.categories"].create({
                "channel_id":channel_id.id,
                "operation":"import"}).get_category_by_id(prestashop, categ_id)
            feed_id = self.env["category.feed"].create(categ_data)
            _logger.info("category feed created with ID %r",feed_id)

    def _get_attribute_name(self, prestashop, attribute_id):
        if prestashop:
            attribute_value = prestashop.get("product_option_values", attribute_id)
            attribute_value_id = attribute_value.get("product_option_value").get("id_attribute_group")
            option_value = prestashop.get("product_options", attribute_value_id)
            option_value = option_value.get("product_option")
            name = ""
            if type(option_value['name']['language'])==list:
                for attr_name in option_value['name']['language']:
                    if attr_name['attrs']['id'] == self.channel_id.ps_language_id:
                        name = attr_name['value']
            else:
                name = option_value.get('name')['language']['value']
            return name

    def _get_attribute(self, prestashop, product_option_value_ids):
        if prestashop:
            vals_list = []
            for value in product_option_value_ids:
                product_value = prestashop.get("product_option_values", value)
                product_value = product_value.get("product_option_value")
                if type(product_value['name']['language'])==list:
                    for attr_name in product_value['name']['language']:
                        if attr_name['attrs']['id'] == self.channel_id.ps_language_id:
                            attrib_name = attr_name['value']
                else:
                    attrib_name = product_value.get('name')['language']['value']
                vals = dict(
                            name = self._get_attribute_name(prestashop,value),
                            value = attrib_name,
                            attrib_name_id = product_value.get("id_attribute_group"),
                            attrib_value_id = value
                        )
                vals_list.append(vals)
            return vals_list

    def _get_feed_variants(self, prestashop, product_data):
        product_id = product_data["id"]
        if prestashop:
            combinations = product_data.get('associations').get("combinations",{}).get("combination")
            vals_list = []
            if combinations:
                if type(combinations)== list:
                    combination_ids = [i['id'] for i in combinations]
                else:
                    combination_ids = [combinations['id']]
                for combination_id in combination_ids:
                    try:
                        combination = prestashop.get("combinations", combination_id)
                    except Exception as e:
                        _logger.info("Error:- %r",str(e))
                        return vals_list
                    combination = combination.get("combination")
                    product_option_value =combination.get("associations").get("product_option_values")
                    product_option_value_id = product_option_value.get("product_option_value")
                    if not product_option_value_id:
                        continue
                    if isinstance(product_option_value_id,list):
                        product_option_value_ids = [ i["id"] for i in product_option_value_id]
                    elif isinstance(product_option_value_id,dict):
                        product_option_value_ids = [product_option_value_id.get("id")]
                    combination_id = combination.get("id")
                    quantity = None
                    try:
                        stock_search = prestashop.get('stock_availables',
                                                    options={'filter[id_product]': product_id, 'filter[id_product_attribute]': combination_id})
                    except Exception as e:
                        _logger.info(
                            "Error :- ----------------> Unable to search given stock id")
                    if isinstance(stock_search,dict) and stock_search.get("stock_availables"):
                        stock_id = stock_search['stock_availables']['stock_available']['attrs']['id']
                        try:
                            stock_data  = prestashop.get("stock_availables",stock_id)
                            quantity = stock_data.get("stock_available",{}).get("quantity")
                        except Exception as e:
                            _logger.info("Stock data not received for combination id %r",combination_id)
                    vals = dict(
                            store_id = combination_id,
                            default_code = combination.get("reference",""),
                            list_price = str(float(combination['price'])+ float(self._context.get('list_price'))),
                            standard_price = combination.get("wholesale_price",""),
                            name_value = self._get_attribute(prestashop, product_option_value_ids),
                            length = product_data.get("length",""),
                            width = product_data.get("width",""),
                            height = product_data.get("height",""),
                            # weight = product_data.get("weight",""),
                            #weight_unit = ,
                            #dimensions_unit = ,
                            wk_product_id_type = "wk_ean",
                            #hs_code = ,
                            barcode = combination.get("ean13",""),
                        )
                    if quantity:
                        vals["qty_available"] = quantity
                    default_image_id = combination.get("associations").get("images",{}).get("image")
                    if isinstance(default_image_id,list):
                        default_image_id = default_image_id[0]["id"]
                    elif isinstance(default_image_id,dict):
                        default_image_id = default_image_id["id"]
                    if isinstance(default_image_id,str):
                        image = self._get_default_image(prestashop, product_id, default_image_id)
                        vals['image'] = image
                    vals_list.append((0,0,vals))
            return vals_list

    def _prestashop_create_product_feed(self, prestashop, product_id):
        if prestashop:
            vals = {}
            try :
                product = prestashop.get("products", product_id)
            except Exception as e:
                _logger.info("Error :- Fetching Product %r",[str(e), product_id])
                return vals
            product = product.get('product')
            if product:
                product_basics = self._get_product_basics(prestashop, product)
                vals.update(product_basics)
                variants = self.with_context(list_price = vals.get('list_price','0.0'))._get_feed_variants(prestashop, product)
                vals["feed_variants"] = variants
                default_image_id = product.get("id_default_image").get('value')
                if product.get("associations").get("images").get("image") and default_image_id:
                        image = self._get_default_image(prestashop, product_id,default_image_id)
                        vals['image'] = image
                feed_obj = self.env['product.feed']
                feed_id = self.channel_id._create_feed(feed_obj, vals)
            return feed_id

    def get_product_by_id(self, prestashop, product_id):
        if prestashop:
            vals = {}
            try :
                product = prestashop.get("products", product_id)
            except Exception as e:
                _logger.info("Error :- Fetching product %r",[str(e), product_id])
                return vals
            if product:
                # _logger.info("=====product id api %r", product)
                product = product.get('product')
                product_basics = self._get_product_basics(prestashop, product)
                vals.update(product_basics)
                # vals["feed_variants"] = [(5,0)]
                variants = self.with_context(list_price = vals.get('list_price','0.0'))._get_feed_variants(prestashop, product)
                vals.update(feed_variants = variants)
            return vals

    def _filter_product_using_date(self, prestashop, channel, product_import_date,page_size):
        if prestashop:
            date_created = None
            vals_list = []
            date = fields.Datetime.to_string(product_import_date)
            limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
            try:
                data =  prestashop.get('products',  options={'filter[date_add]':'>['+date+']', 'date':1,'limit':limit})
                data = data.get("products")
                if isinstance(data,str):
                    return vals_list,date_created
            except Exception as e:
                _logger.info("=====> Error while fetching products : %r.", e)
            else:
                data = data.get("product")
                if isinstance(data,list) and len(data):
                    for product_data in data:
                        product_id = product_data['attrs']['id']
                        vals = self.get_product_by_id(prestashop,product_id)
                        if vals:
                            vals_list.append(vals)
                    last_product_id = data[-1]["attrs"]["id"]
                    last_product = prestashop.get("products",last_product_id)
                    date_created = last_product.get("product",{}).get("date_add")
                elif isinstance(data,dict):
                    product_id = data['attrs']['id']
                    vals = self.get_product_by_id(prestashop,product_id)
                    if vals:
                        vals_list.append(vals)
                    last_product = prestashop.get("products",product_id)
                    date_created = last_product.get("product",{}).get("date_add")
            return vals_list, date_created

    def get_product_all(self, prestashop,page_size):
        if prestashop:
            vals_list = []
            limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
            products = prestashop.get("products",options={'limit':limit})
            products = products.get("products")
            if isinstance(products, str):
                return vals_list
            products = products.get("product")
            if isinstance(products, list):
                for product in products:
                    vals = {}
                    product_id = product.get("attrs").get("id")
                    vals = self.get_product_by_id(prestashop,product_id)
                    if not vals:continue
                    vals_list.append(vals)
            elif isinstance(products,dict):
                product_id = products.get("attrs").get("id")
                vals = self.get_product_by_id(prestashop,product_id)
                if vals:
                    vals_list.append(vals)
            return vals_list

    def import_now(self,**kwargs):
        data_list = []
        prestashop = self._context.get('prestashop')
        page_size = kwargs.get("page_size")
        prestashop_object_id = kwargs.get('prestashop_object_id')
        channel = self.channel_id
        product_import_date = kwargs.get('prestashop_import_date_from')
        if prestashop_object_id:
            vals = self.get_product_by_id(prestashop, prestashop_object_id)
            if vals:
                data_list.append(vals)
        elif product_import_date:
            data_list, last_added = self._filter_product_using_date(
                prestashop,channel,product_import_date,page_size)
            kwargs["last_added"] = last_added
        else:
            data_list = self.get_product_all(prestashop,page_size)
        return data_list,kwargs