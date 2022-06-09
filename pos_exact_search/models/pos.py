# -*- coding: utf-8 -*-


from odoo import fields, models,tools,api


class pos_config(models.Model):
    _inherit = 'pos.config' 
    
    allow_exact_search = fields.Boolean("Allow Exact Search")

    