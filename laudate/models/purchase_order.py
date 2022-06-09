# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _get_product_purchase_description(self, product_lang):
        seller_line = self.product_id.variant_seller_ids.filtered(lambda p:p.name.id == self.order_id.partner_id.id and p.product_id == self.product_id)
        if seller_line and seller_line[0].product_code:
            return "[%s] [%s] %s"%(self.product_id.default_code, seller_line[0].product_code,self.product_id.name)
        return super(PurchaseOrderLine, self)._get_product_purchase_description(product_lang)



