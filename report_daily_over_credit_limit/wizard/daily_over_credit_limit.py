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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import fields, osv


class daily_over_credit_limit(osv.osv_memory):

    _name = 'daily.over.credit.limit'
    _description = 'Daily Over Credit Limit'

    _columns = {
        'date': fields.date('Date', required=True),
        'credit_limit': fields.float('Credit Limit', required=True),
        'partner_ids': fields.many2many('res.partner', 'daily_over_credit_limit_partner_rel', 'report_id', 'partner_id', 'Partners', domain=[('supplier', '=', True)], required=True),
    }
    _defaults = {
        'date': lambda *a: (datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d') + relativedelta(days=1)).strftime('%Y-%m-%d'),
        'partner_ids': [(6, 0, [46, 47])],
    }

    def _get_credit_limit(self, cr, uid, ids):
        results = self.pool.get('res.partner').read(cr, uid, ids, ['debit_limit'])
        return sum([result['debit_limit'] for result in results])

    def onchange_partner_ids(self, cr, uid, ids, value, context=None):
        res = {'value': {}}
        if not value or not value[0] or not value[0][0] == 6:
            return
        credit_limit = self._get_credit_limit(cr, uid, value[0][2])
        res.update({'value': {'credit_limit': credit_limit}})
        return res

    def start_report(self, cr, uid, ids, data, context=None):
        for wiz_obj in self.read(cr, uid, ids):
            if 'form' not in data:
                data['form'] = {}
            data['form']['date'] = wiz_obj['date']
            data['form']['credit_limit'] = wiz_obj['credit_limit']
            data['form']['partner_ids'] = wiz_obj['partner_ids']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'daily_over_credit_limit',
            'datas': data,
        }

daily_over_credit_limit()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
