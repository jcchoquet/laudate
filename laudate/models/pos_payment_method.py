# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    bank_journal_id = fields.Many2one('account.journal', string="Bank Journal",
                                      domain=[('type', 'in', ['cash','bank'])])
    