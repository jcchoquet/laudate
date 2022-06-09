# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):
        param_strict = self.env['ir.config_parameter'].sudo().get_param('adopte.reservation_location_strict',False)
        
        return super(StockQuant, self)._update_reserved_quantity(product_id, location_id, quantity, lot_id, package_id, owner_id, strict=param_strict)