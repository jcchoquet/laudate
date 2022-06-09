# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#    See LICENSE file for full copyright and licensing details.
#################################################################################

from odoo import api, fields, models, _
from odoo import tools
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def multichannel_sync_quantity(self, pick_details):
        channel_list = self._context.get('channel_list', [])
        channel_list.append('prestashop')
        return super(StockMove, self.with_context({
            "channel_list": channel_list
        })).multichannel_sync_quantity(pick_details)
