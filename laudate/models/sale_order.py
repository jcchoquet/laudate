# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    store_order_id = fields.Char("Id Commande Site",compute='compute_store_order_id', store=True)
    state_picking = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Statut BL', compute='_compute_state_picking_ids',
        copy=False, index=True, readonly=True, store=True, tracking=True)    
    
    @api.depends('channel_mapping_ids')
    def compute_store_order_id(self):
        for order_id in self:
            order_id.store_order_id = ''
            mapping_ids = order_id.channel_mapping_ids
            if mapping_ids:
                order_id.store_order_id = mapping_ids[0].store_order_id


    @api.depends('picking_ids')
    def _compute_state_picking_ids(self):
        for order in self:          
            pickings = order.picking_ids.filtered(lambda x: x.state not in ('draft','cancel'))       
            order.state_picking = pickings and pickings[0].state or False
            
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    delivered_by_hand = fields.Boolean("Remis en main propre")