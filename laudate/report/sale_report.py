from odoo import tools
from odoo import api, fields, models

class SaleReport(models.Model):
    _inherit = "sale.report"

    default_code = fields.Char('Référence interne', readonly=True)
    
    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['default_code'] = ", p.default_code as default_code"
        
        groupby += ', p.default_code'

        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
    