# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

class ir_mail_server(models.Model):

    _inherit = "ir.mail_server"

    user_id = fields.Many2one('res.users', string="User")
    company_ids = fields.Many2many('res.company','ir_mail_server_rel','mail_server_id','company_id', string="Company")
    is_smtp_by_company = fields.Boolean("Is SMTP by Company", default=False)
    smtp_from = fields.Char(string='Email From',help='Set this in order to email from a specific address.')

    @api.model
    def default_get(self, fields):
        res = super(ir_mail_server, self).default_get(fields)
        res_config_company = self.env['res.config.settings'].search([],order='id desc', limit=1)
        if res_config_company.smtp_by_company == True:
            res.update({'is_smtp_by_company':True})
        return res

    @api.model
    def send_email(self, message, mail_server_id=None, smtp_server=None, smtp_port=None,
                   smtp_user=None, smtp_password=None, smtp_encryption=None, smtp_debug=False,
                   smtp_session=None):
        mail_server = None
        if mail_server_id:
            mail_server = self.with_user(SUPERUSER_ID).browse(mail_server_id)
        elif not smtp_server:
            mail_server = self.with_user(SUPERUSER_ID).search([], order='sequence', limit=1)

        if mail_server and mail_server.smtp_from:
            split_from = message['From'].rsplit(' <', 1)
            if len(split_from) > 1:
                email_from = '%s <%s>' % (split_from[0], mail_server.smtp_from, )
            else:
                email_from = mail_server.smtp_from
            message.replace_header('From', email_from)
            
            bounce_alias = self.env['ir.config_parameter'].with_user(SUPERUSER_ID).get_param("mail.bounce.alias")
            if not bounce_alias:
                # then, bounce handling is disabled and we want
                # Return-Path = From
                if 'Return-Path' in message:
                    message.replace_header('Return-Path', email_from)
                else:
                    message.add_header('Return-Path', email_from)

        return super(ir_mail_server, self).send_email(message, mail_server_id, smtp_server, smtp_port,
            smtp_user, smtp_password, smtp_encryption, smtp_debug, smtp_session)
