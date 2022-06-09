# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class PaymentReport(models.Model):
    _name = "payment.report"
    _description = "Payment Report"
    _auto = False    
    
    date = fields.Date('Date', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    team_id = fields.Many2one('crm.team', string='Equipe', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    amount = fields.Float('montant', readonly=True)
    
    
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        with_ = ("WITH %s" % with_clause) if with_clause else ""

        with_ = """
            WITH all_payment AS (
                SELECT pp.payment_date, u.sale_team_id, pp.create_uid, ppm.bank_journal_id as journal_id, sum(amount) as amount
                from pos_payment pp
                INNER JOIN pos_payment_method ppm ON ppm.id = pp.payment_method_id
                INNER JOIN res_users u on u.id = pp.create_uid
                GROUP BY pp.payment_date, u.sale_team_id, pp.create_uid, ppm.bank_journal_id
                UNION
                SELECT ap.payment_date, u.sale_team_id, ap.create_uid, ap.journal_id, sum(case when payment_type = 'inbound' then amount else -amount end) as amount
                from account_payment ap
                INNER JOIN res_users u on u.id = ap.create_uid
                where ap.state not in('draft','cancelled') and ap.name not like 'POS%' and ap.partner_type = 'customer'
                GROUP BY ap.payment_date, u.sale_team_id, ap.create_uid, ap.journal_id
                )
        """

        select_ = """
            min(aj.id) as id,
            pp.payment_date as date,
            pp.journal_id,
            pp.sale_team_id as team_id,
            pp.create_uid as user_id,
			aj.company_id as company_id,
            sum(amount) as amount           
        """

        for field in fields.values():
            select_ += field

        from_ = """
                account_journal aj                
                INNER JOIN all_payment pp ON pp.journal_id = aj.id                
                %s
        """ % from_clause

        groupby_ = """
            pp.payment_date,
            pp.journal_id,
            pp.sale_team_id,
            pp.create_uid,
			aj.company_id
            %s
        """ % (groupby)

        return """%s (SELECT %s FROM %s WHERE aj.type in ('cash','bank') GROUP BY %s)""" % (with_, select_, from_, groupby_)
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))
