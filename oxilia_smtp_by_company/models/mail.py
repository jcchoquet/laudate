# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class Mail(models.Model):
    _inherit = "mail.mail"

    @api.model
    def create(self, vals):
        context = self._context        
        company = False
        company = self.env.company
        
        if context.get('active_model') == 'res.partner' and context.get('active_id'):
            partner = self.env['res.partner'].browse(context['active_id'])
            if partner:
                company = partner.company_id
        
        if company:
            ICPSudo = self.env['ir.config_parameter'].with_user(SUPERUSER_ID)
            smtp_by_company = bool(ICPSudo.get_param('oxilia_smtp_by_company.smtp_by_company'))
            
            if smtp_by_company:
                out_mail_sever = self.env['ir.mail_server'].with_user(SUPERUSER_ID).search([('company_ids', '=', company.id)], limit=1)
            else:
                return super(Mail, self).create(vals)

            if out_mail_sever:
                vals.update({'mail_server_id': out_mail_sever.id, 'reply_to':out_mail_sever.smtp_from})
             
        return super(Mail, self).create(vals)

class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def create(self, vals):        
        if 'mail_server_id' not in vals:
            active_company_id = self.env.company and self.env.company.id
            mail_server = self.env['ir.mail_server'].with_user(SUPERUSER_ID).search([('is_smtp_by_company', '=', True)])
            if mail_server:
                out_mail_sever = self.env['ir.mail_server'].with_user(SUPERUSER_ID).search([])
                for mail_server in out_mail_sever:
                    for company in mail_server.company_ids:
                        if active_company_id == company.id:
                            vals.update({'mail_server_id': mail_server.id})
        
        return super(MailMessage, self).create(vals)

