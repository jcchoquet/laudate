# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

from odoo.addons.prestashop_odoo_bridge.models.prestapi import PrestaShopWebService,PrestaShopWebServiceDict
_logger = logging.getLogger(__name__)


class ExportPrestashopAttribute(models.TransientModel):
    _inherit = 'export.operation'
    _name = "export.prestashop.attribute"
    _description = "Export Prestashop Attributes"


    @api.model
    def export_now(self, record):
        prestashop = self._context.get('prestashop')
        channel_id = self._context.get('channel_id')
        create_dim_opt = None
        try:
            add_data = prestashop.get(
                'product_options', options={'schema': 'blank'})
            add_value = prestashop.get(
                'product_option_values', options={'schema': 'blank'})
            attribute_id = record.attribute_id
            mapping_obj = self.env['channel.attribute.mappings']
            is_mapped = mapping_obj.search([
                ('channel_id', '=', channel_id.id),
                ('odoo_attribute_id', '=', attribute_id.id)
            ])
            if not is_mapped:
                name = attribute_id.name
                presta_id = self.create_dimension_type(
                    prestashop,channel_id, add_data, attribute_id, name)
            else:
                presta_id = is_mapped.store_attribute_id
            attrib_value_map = self.env['channel.attribute.value.mappings'].search([
                ('channel_id', '=', self.channel_id.id),
                ('odoo_attribute_value_id', '=', record.id)])
            if not attrib_value_map:
                create_dim_opt = self.create_dimension_option(prestashop, channel_id,
                    add_value, presta_id, record, record.name)
            else:
                create_dim_opt = attrib_value_map.store_attribute_value_id
        except Exception as e:
            _logger.info("%r",str(e))
            if channel_id.debug == "enable":
                raise UserError(_('Error %s') % str(e))
            return False
        return create_dim_opt

    def create_dimension_type(self, prestashop, channel_id, add_data, erp_dim_type_id, name):
        add_data['product_option'].update({
                                    'group_type': 'select',
                                    'position':'0'
                                })
        if type(add_data['product_option']['name']['language']) == list:
            for i in range(len(add_data['product_option']['name']['language'])):
                add_data['product_option']['name']['language'][i]['value'] = name
                add_data['product_option']['public_name']['language'][i]['value'] = name
        else:
            add_data['product_option']['name']['language']['value'] = name
            add_data['product_option']['public_name']['language']['value'] = name
        try:
            returnid = prestashop.add('product_options', add_data)
            channel_id.create_attribute_mapping(erp_dim_type_id, returnid)
            self._cr.commit()
            _logger.info("returnid ==========> %r",returnid)
        except Exception as e:
            if channel_id.debug == "enable":
                raise UserError("Error in creating Dimension Type (ID: %s).%s"%(erp_dim_type_id.id,str(e)))
            return False
        return returnid

    def update_dimension_type(self, prestashop, presta_id, name):
        try:
            update_data = prestashop.get('product_options', presta_id)
            if type(update_data['product_option']['name']['language']) == list:
                for i in range(len(update_data['product_option']['name']['language'])):
                    update_data['product_option']['name']['language'][i]['value'] = name
                    update_data['product_option']['public_name']['language'][i]['value'] = name
            else:
                update_data['product_option']['name']['language']['value'] = name
                update_data['product_option']['public_name']['language']['value'] = name
            returnid = prestashop.edit('product_options', presta_id, update_data)
        except Exception as e:
            _logger.info("Error in updating Dimension Type : %r",str(e))
            return False
        return returnid

    def create_dimension_option(self, prestashop, channel_id, add_value, presta_attr_id,erp_dim_opt_id, name):
        add_value['product_option_value'].update({
                                    'id_attribute_group': presta_attr_id,
                                    'position':'0'
                                })
        if type(add_value['product_option_value']['name']['language']) == list:
            for i in range(len(add_value['product_option_value']['name']['language'])):
                add_value['product_option_value']['name']['language'][i]['value'] = name
        else:
            add_value['product_option_value']['name']['language']['value'] = name
        try:
            returnid = prestashop.add('product_option_values', add_value)
            channel_id.create_attribute_value_mapping(erp_dim_opt_id, returnid)
            self._cr.commit()
        except Exception as e:
            if self.channel_id.debug == "enable":
                raise UserError('Error creating Dimension Option(ID: %s.%s' % (str(erp_dim_opt_id.id),str(e)))
            return False
        return returnid

    def update_dimension_option(self, prestashop, prestashop_atrib_val_id, name):
        attibute_option = False
        try:
            attibute_option = prestashop.get("product_option_values", prestashop_atrib_val_id)
            if type(attibute_option['product_option_value']['name']['language']) == list:
                for i in range(len(attibute_option['product_option_value']['name']['language'])):
                    attibute_option['product_option_value']['name']['language'][i]['value'] = name
            else:
                attibute_option['product_option_value']['name']['language']['value'] = name
            returnid = prestashop.edit('product_option_values', prestashop_atrib_val_id ,attibute_option)
        except Exception as e:
            _logger.info("Error in updating Product Option Values : %r",str(e))
            return False
        return returnid