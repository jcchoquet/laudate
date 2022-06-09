import logging
_logger = logging.getLogger(__name__)
from odoo import models, fields, api

class ImportPrestashopShipping(models.TransientModel):
    _name = "import.prestashop.shipping"
    _inherit = "import.operation"
    _description = "Import Prestashop Shipping"

    def import_now(self,**kwargs):
        data_list = []
        prestashop = self._context.get("prestashop")
        channel_id = self.channel_id
        page_size = kwargs.get("page_size")
        prestashop_object_id = kwargs.get("prestashop_object_id")
        if prestashop_object_id:
            vals = self.get_shipping_vals(channel_id, prestashop, prestashop_object_id)
            if isinstance(vals,dict):
                data_list.append(vals)
        else:
            data_list = self.get_shipping_all(prestashop, channel_id,page_size)
        return data_list, kwargs

    def get_shipping_all(self,prestashop ,channel_id,page_size):
        vals_list = []
        limit = '{},{}'.format(str(page_size),str(self.channel_id.api_record_limit))
        try:
            shipping_data = prestashop.get("carriers", options={'limit':limit})
            shipping_data = shipping_data.get("carriers")
            if isinstance(shipping_data,str):
                return vals_list
        except Exception as e:
            _logger.info("ShippingError ======> %r",str(e))
        else:
            shipping_ids = shipping_data.get("carrier")
            if isinstance(shipping_ids,list):
                _logger.info("shipping_Data =======> %r",shipping_data)
                vals_list = list(map(lambda x: self.get_shipping_vals(channel_id,prestashop,x.get("attrs",{}).get("id")),shipping_ids))
        return vals_list

    def get_shipping_vals(self, channel_id, prestashop, shipping_id):
        if shipping_id:
            try:
                shipping_data = prestashop.get("carriers",shipping_id)
            except Exception as e:
                _logger.info("Shipping Error ==========> %r",str(e))
            else:
                return {
                    "name": shipping_data["carrier"].get("name"),
                    "store_id": shipping_data["carrier"].get("id"),
                    "shipping_carrier": shipping_data["carrier"].get("name"),
                    "channel_id": channel_id.id,
                    "channel": channel_id.channel,
                    "description": shipping_data["carrier"].get("description",False)
                    }
