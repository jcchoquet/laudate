# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class GoldPRice(models.Model):
    _name = "gold.price"
    _description = "Cours Or"
    _order = 'date desc, id desc'
    
    date = fields.Date("Date", default=fields.Date.today())
    price = fields.Float('Cours Or (Prix au Kg)', digits='Product Price')