# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    
    
    default_code = fields.Char('Référence interne',readonly=True, related='product_id.default_code', store=True)
    