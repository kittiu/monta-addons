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


class daily_trade_summary(osv.osv_memory):

    _name = 'daily.trade.summary'
    _description = 'Daily Over Credit Limit'

    _columns = {
        'date': fields.date('Date', required=True),
    }
    _defaults = {
        'date': lambda *a: (datetime.strptime(time.strftime('%Y-%m-%d'), '%Y-%m-%d')).strftime('%Y-%m-%d'),
    }

    def start_report(self, cr, uid, ids, data, context=None):
        for wiz_obj in self.read(cr, uid, ids):
            if 'form' not in data:
                data['form'] = {}
            data['form']['date'] = wiz_obj['date']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'daily_trade_summary',
            'datas': data,
        }

daily_trade_summary()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
