# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv


class report_thai_tax_wizard(osv.osv_memory):

    _name = 'report.thai.tax.wizard'

    def onchange_tax_id(self, cr, uid, ids, tax_id, context=None):
        if not tax_id:
            return {'value': {}}
        tax = self.pool.get('account.tax').browse(cr, uid, tax_id, context)
        return {'value': {'base_code_id': tax.base_code_id.id,
                         'tax_code_id': tax.tax_code_id.id,
                         'type_tax_use': tax.type_tax_use, }}

    def _get_company(self, cr, uid, context=None):
        user_pool = self.pool.get('res.users')
        company_pool = self.pool.get('res.company')
        user = user_pool.browse(cr, uid, uid, context=context)
        company_id = user.company_id
        if not company_id:
            company_id = company_pool.search(cr, uid, [])
        else:
            company_id = company_id.id
        return company_id or False

    def _get_period(self, cr, uid, context=None):
        """Return default period value"""
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'period_id': fields.many2one('account.period', 'Period', required=True),
        'tax_id': fields.many2one('account.tax', 'Tax', domain=[('type_tax_use', 'in', ('sale', 'purchase')), ('is_wht', '=', False), ], required=True),
        'base_code_id': fields.many2one('account.tax.code', 'Base Code', domain=[('id', '=', False)], required=True),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Code', required=True),
        'type_tax_use': fields.selection([('sale', 'Sale'), ('purchase', 'Purchase'), ('all', 'All')], 'Tax Application', required=True)
    }

    _defaults = {
        'company_id': _get_company,
        'period_id': _get_period,
    }

    def start_report(self, cr, uid, ids, data, context=None):
        for wiz_obj in self.read(cr, uid, ids):
            if 'form' not in data:
                data['form'] = {}
            data['form']['company_id'] = wiz_obj['company_id'][0]
            data['form']['period_id'] = wiz_obj['period_id'][0]
            data['form']['tax_id'] = wiz_obj['tax_id'][0]
            data['form']['base_code_id'] = wiz_obj['base_code_id'][0]
            data['form']['tax_code_id'] = wiz_obj['tax_code_id'][0]
            data['form']['type_tax_use'] = wiz_obj['type_tax_use']
            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'monta_report_thai_tax',
                    'datas': data,
            }

report_thai_tax_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
