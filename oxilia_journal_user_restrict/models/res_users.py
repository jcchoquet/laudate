# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Allowed account journal',
        help="Allowed account journal for users. POS managers can view all Points of Sale.",
    )

    def write(self, values):
        res = super(ResUsers, self).write(values)
        if 'journal_ids' in values:
            self.env['ir.default'].clear_caches()
        return res
