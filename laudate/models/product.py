# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    price_ttc = fields.Float('Prix TTC', compute='_compute_product_price_ttc', digits='Product Price')
    price_make = fields.Float('Prix façon', digits='Product Price')

    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """
        name = self.display_name        
        
        # if self.description_sale:
            # name += '\n' + self.description_sale

        return name
        
    @api.depends_context('pricelist', 'partner', 'quantity', 'uom', 'date', 'no_variant_attributes_price_extra')
    def _compute_product_price_ttc(self):
        prices = {}
        pricelist_id_or_name = "Liste de prix publique"
        if pricelist_id_or_name:
            pricelist = None
            partner = self.env.context.get('partner', False)
            quantity = self.env.context.get('quantity', 1.0)

            # Support context pricelists specified as list, display_name or ID for compatibility
            if isinstance(pricelist_id_or_name, list):
                pricelist_id_or_name = pricelist_id_or_name[0]
            if isinstance(pricelist_id_or_name, str):
                pricelist_name_search = self.env['product.pricelist'].name_search(pricelist_id_or_name, operator='=', limit=1)
                if pricelist_name_search:
                    pricelist = self.env['product.pricelist'].browse([pricelist_name_search[0][0]])
            elif isinstance(pricelist_id_or_name, int):
                pricelist = self.env['product.pricelist'].browse(pricelist_id_or_name)

            if pricelist:
                quantities = [quantity] * len(self)
                partners = [partner] * len(self)
                prices = pricelist.get_products_price(self, quantities, partners)

        for product in self:            
            price = prices.get(product.id, 0.0)
            taxes = product.taxes_id.compute_all(price, product.company_id.currency_id, 1, product=product, partner=partner)
            product.price_ttc = taxes['total_included']         
        
    def compute_standard_price_gold(self):
        """ on récupère le cours de l'or (prix au kilo) en foncion de la date de calcul
            formule de calcul : grammage du produit * prix de l'or au gramme * 751/1000 * 1,06 = prix de l'or
            + prix facon
        """
        today = fields.Date.today()
        gold_price = self.env["gold.price"].search([('date', '<=', today)], limit=1)
        if not gold_price:
            raise UserError(_("Aucun prix d'or trouvé. Veuillez vérifier le paramétrage."))
        
        for product in self.search(['|',('weight', '!=', False),('price_make','!=',False)]):
            product.standard_price = (product.weight * (gold_price.price/1000) * 751/1000 * 1.06) + product.price_make     
        
        
class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"       
        
    def _is_from_single_value_line(self, only_active=True):
        """Return whether `self` is from a single value line, counting also
        archived values if `only_active` is False.
        """
        self.ensure_one()
        all_values = self.attribute_line_id.product_template_value_ids
        if only_active:
            all_values = all_values._only_active()
        return len(all_values) == 0