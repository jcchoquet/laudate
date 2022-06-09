# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from itertools import repeat
import logging
_logger = logging.getLogger(__name__)

class PrintMulitpleLabelProduct(models.TransientModel):
    _name = "print.multiple.label.product"
    _description = "Print Multiple lable product"

    nb_print = fields.Integer("Nombre d'étiquettes à imprimer", default=1)

    def print_multiple_label(self):
        ids = [x for item in self.env.context.get('active_ids', []) for x in repeat(item, self.nb_print)]
        return self.env.ref('laudate.report_product_label_wizard').report_action(ids)
