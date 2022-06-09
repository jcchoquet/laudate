# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    smtp_by_company = fields.Boolean(string="SMTP BY COMPANY", default=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].with_user(SUPERUSER_ID)
        smtp_by_company = ICPSudo.get_param('oxilia_smtp_by_company.smtp_by_company')

        res.update(smtp_by_company = smtp_by_company,)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].with_user(SUPERUSER_ID)
        ICPSudo.set_param("oxilia_smtp_by_company.smtp_by_company", self.smtp_by_company)
        
        mail_server_config = self.env['ir.mail_server'].with_user(SUPERUSER_ID).search([])
        for mail_server in mail_server_config:
            mail_server.is_smtp_by_company =  self.smtp_by_company            
