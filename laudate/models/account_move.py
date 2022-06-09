# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class MoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id

        values = []
        if product.partner_ref:
            values.append(product.partner_ref)
        if self.journal_id.type == 'sale':
            values.append(product.name)
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)

    def import_ecritures_VE(self, year):
        company_id = self.env.company.id
        user_id = self.env.user.id
               
        _logger.info("DEBUT IMPORT ECRITURE VT")   
        
        pieceprec = ''
        move_id = False
        # création des pieces comptables
        self.env.cr.execute("""select * from IMPORT_ECRITURE where journal = 'VT' and substr(date,5,4) = '%s' order by journal,piece;""" % year)
        for row in self.env.cr.dictfetchall():
            if pieceprec != row['piece']:
                if move_id:
                    move_id.post()
            
                partner_id = False
                #creation de la piece comptables
                values = {
                    'date': datetime.strptime(row['date'],'%d%m%Y'),
                    'journal_id': self.env['account.journal'].search([('company_id', '=', company_id),('code','=','FAC'), ('type','=', 'sale')]).id,
                    'company_id': company_id,
                    'ref': row['piece'],
                    'name': row['piece']
                }
                move_id = self.env['account.move'].create(values)
                
            account_id = self.env['account.account'].search([('company_id', '=', company_id),('code','=',row['compte'])])
            if not account_id and row['compte'][:1] == '4':
                vals_compte_comptable = {
                    'code': row['compte'],
                    'name': row['compte'],
                    'user_type_id': self.env['account.account.type'].search([('type','=','receivable')],limit=1).id,
                    'reconcile': True,
                    'company_id': company_id,              
                }
                account_id = self.env['account.account'].create(vals_compte_comptable)
                
            if row['compte'][:2] == '41' and row['num_client']:
                try:
                    float(row['num_client'][4:]).is_integer()
                    # _logger.info("CLIENT INT %r",int(row['num_client'][4:]))
                    partner = self.env['ir.model.data'].search([('model','=','res.partner'),('name','=',int(row['num_client'][4:]))],limit=1)
                    partner_id = partner and partner.res_id or False
                except Exception as e:
                    _logger.info("CLIENT STR %r",row['num_client'])
                    partner = self.env['res.partner'].search([('name','=',row['num_client'])],limit=1)
                    partner_id = partner and partner.id or False
            
            move_id.partner_id = partner_id
                            
            values_line = {
                'account_id': account_id.id,
                'partner_id' : partner_id,
                'name': row['libelle'],
                'debit': float(row['montant'].replace(',','.')) if row['sens'] == 'D' else 0.0,
                'credit': float(row['montant'].replace(',','.')) if row['sens'] == 'C' else 0.0,
                'date_maturity': datetime.strptime(row['date'],'%d%m%Y'),
                'move_id': move_id.id,
            }
            _logger.info("LINE %r %r",values_line, row['piece'])
            self.env['account.move.line'].with_context(check_move_validity=False).create(values_line)
            
            pieceprec = row['piece']
            
            
        if move_id:
            move_id.post()
            
        _logger.info("FIN IMPORT ECRITURE VE")
        
    def import_ecritures_banque(self, year):
        company_id = self.env.company.id
        user_id = self.env.user.id
        
        _logger.info("DEBUT IMPORT ECRITURE BANQUE")   
        
        pieceprec = ''
        # création des pieces comptables
        self.env.cr.execute("""select * from IMPORT_REGLEMENT where substr(compte,1,1)= '4' and substr(date,5,4) = '%s';""" % year)
        for row in self.env.cr.dictfetchall():
            journal = self.env['account.journal'].search([('company_id', '=', company_id),('type','=','bank'),('code','=','RE')])
                        
            partner_id = False
            #creation de la piece comptable
            values = {
                'date': datetime.strptime(row['date'],'%d%m%Y'),
                'journal_id': journal.id,
                'company_id': company_id,
                'ref': row['libelle']
            }
            move_id = self.env['account.move'].create(values)
            
            account_id = self.env['account.account'].search([('company_id', '=', company_id),('code','=',row['compte'])])
            if not account_id and row['compte'][:1] == '4':
                vals_compte_comptable = {
                    'code': row['compte'],
                    'name': row['libelle'],
                    'user_type_id': self.env['account.account.type'].search([('type','=','receivable')],limit=1).id,
                    'reconcile': True,
                    'company_id': company_id,              
                }
                account_id = self.env['account.account'].create(vals_compte_comptable)
                
            account_banque_id = self.env['account.account'].search([('company_id', '=', company_id),('code','=',row['cpt_banque'])])
                       
            if row['compte'][:2] == '41' and row['num_client']:
                try:
                    float(row['num_client'][4:]).is_integer()
                    # _logger.info("CLIENT INT %r",int(row['num_client'][4:]))
                    partner = self.env['ir.model.data'].search([('model','=','res.partner'),('name','=',int(row['num_client'][4:]))],limit=1)
                    partner_id = partner and partner.res_id or False
                except Exception as e:
                    _logger.info("CLIENT STR %r",row['num_client'])
                    partner = self.env['res.partner'].search([('name','=',row['num_client'])],limit=1)
                    partner_id = partner and partner.id or False
            
            values_line = {
                'account_id': account_id.id,
                'partner_id' : partner_id,
                'name': row['libelle'],
                'debit': float(row['montant'].replace(',','.')) if row['sens'] == 'D' else 0.0,
                'credit': float(row['montant'].replace(',','.')) if row['sens'] == 'C' else 0.0,
                'date_maturity': datetime.strptime(row['date'],'%d%m%Y'),
                'move_id': move_id.id,
            }           
            move_line_id = self.with_context(check_move_validity=False).create(values_line)
            
            values_line = {
                'account_id': account_banque_id.id,
                'partner_id' : partner_id,
                'name': row['libelle'],
                'debit': float(row['montant'].replace(',','.')) if row['sens'] == 'C' else 0.0,
                'credit': float(row['montant'].replace(',','.')) if row['sens'] == 'D' else 0.0,
                'date_maturity': datetime.strptime(row['date'],'%d%m%Y'),
                'move_id': move_id.id
            }           
            self.with_context(check_move_validity=False).create(values_line)
            move_id.post()
            
        _logger.info("FIN IMPORT ECRITURE BANQUE")
        
class AccountMove(models.Model):
    _inherit = 'account.move'
        
    def post(self):
        result = super(AccountMove, self).post()
        ## on met à jour l'onglet achats des produits concernés.
        for move in self:
            if move.type == 'in_invoice':
                for line in move.invoice_line_ids:
                    supplier_info = self.env['product.supplierinfo'].sudo().search([
                        ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), ('product_id', '=', line.product_id.id),
                        ('name', '=', move.partner_id.id),
                    ])
                    if supplier_info:
                        supplier_info.write({'date_start': move.invoice_date, 'price': line.price_unit})
        
        return result