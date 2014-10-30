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
from openerp.report import report_sxw


class report_daily_over_credit_limit(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_daily_over_credit_limit, self).__init__(cr, uid, name, context=context)
        self.get_lines = []
        self.get_products = []
        self.get_total_row = {}
        self.credit_limit = 0.0
        self.credit_spent = 0.0
        self.credit_balance = 0.0
        self.suggested_po = 0.0
        self.over_credit = 0.0
        self.localcontext.update({
            'time': time,
            'init_data': self._init_data,
            'get_lines': self._get_lines,
            'get_products': self._get_products,
            'get_total_row': self._get_total_row,
            'get_credit_limit': self._get_credit_limit,
            'get_credit_spent': self._get_credit_spent,
            'get_credit_balance': self._get_credit_balance,
            'get_suggested_po': self._get_suggested_po,
            'get_over_credit': self._get_over_credit,
            'get_partners': self._get_partners,
        })

    def _init_data(self, form):

        partner_ids = form['partner_ids']

        ################################# Forecast Total Payable #################################
        partner_names = {}
        res = {}
        date_total = {}
        res.update({'prevdue': {}})
        date_total.update({'prevdue': 0.0})
        for partner in self.pool.get('res.partner').browse(self.cr, self.uid, partner_ids):
            partner_names.update({partner.id: partner.name})
            res['prevdue'].update({partner.id: {'total': partner.debit}})
            date_total.update({'prevdue': date_total['prevdue'] + partner.debit})

        # Get total for each partner for selected date
        res.update({'date_selected': {}})
        date_total.update({'date_selected': 0.0})
        query = """
            SELECT rp.id, COALESCE(SUM(l.credit-l.debit), 0.0) total
            FROM res_partner rp
            LEFT OUTER JOIN account_move_line l ON l.partner_id = rp.id
            AND l.reconcile_id IS NULL AND l.state <> 'draft' AND l.date_maturity <= %s
            LEFT OUTER JOIN account_account a ON (l.account_id=a.id) AND a.type IN ('payable')
            WHERE rp.id IN %s
            GROUP BY rp.id, a.type
        """
        self.cr.execute(query, (form['date'], tuple(partner_ids),))
        partners = self.cr.dictfetchall()
        for partner in partners:
            res['date_selected'].update({partner['id']: {'total': partner['total']}})
            # Total of each date (column_total)
            date_total.update({'date_selected': date_total['date_selected'] + partner['total']})

        # Transform to list
        res_trans = []
        top_row = {'id': 0, 'name': 'Σ'}  # Prepare total amount as first row
        top_row_total = 0.0
        for partner_id in partner_ids:  # For normal rows
            row = {'id': partner_id, 'name': partner_names[partner_id]}
            cell_total = res['date_selected'][partner_id]['total']
            row.update({'date_selected': cell_total})
            row.update({'prevdue': res['prevdue'][partner_id]['total'],
                        'row_total': res['prevdue'][partner_id]['total'] - cell_total})  # Add row total
            res_trans.append(row)
        top_row.update({'date_selected': date_total['date_selected']})
        top_row_total += date_total['date_selected']
        top_row.update({'prevdue': date_total['prevdue'],
                        'row_total': date_total['prevdue'] - top_row_total})
        res_trans.insert(0, top_row)  # Insert top row

        ################################# Main Table #################################
        res_table = []
        total_row = {'id': False, 'name': False, 'quantity': 0.0, 'onhand': 0.0, 'suggested_qty': 0.0, 'price_unit': False, 'amount': 0.0}
        # Building the product list
        query = """
            select id, name, coalesce(quantity, 0) quantity from
            (select pp.id, pt.name, sum(product_qty) quantity from
            product_product pp join product_template pt on pt.id = pp.product_tmpl_id
                and pp.active = True and sale_ok = True
            left outer join stock_move sm on sm.product_id = pp.id
                and sm.state in ('waiting', 'confirmed', 'assigned', 'done')
                and sm.date_expected >= %s and sm.date_expected <= %s
            left outer join stock_picking sp on sp.id = sm.picking_id and sp.type = 'out'
            group by pp.id, pt.name
            ) a order by id
        """
        self.cr.execute(query, (form['date'] + ' 00:00:00', form['date'] + ' 23:59:59',))
        products = self.cr.dictfetchall()
        for product in products:
            prod = self.pool.get('product.product').browse(self.cr, self.uid, product['id'])
            row = {'id': product['id'], 'name': product['name'], 'quantity': product['quantity'],
                   'onhand': prod.qty_available or 0.0}
            row.update({'suggested_qty': row['quantity'] - row['onhand'] >= 0.0 and row['quantity'] - row['onhand'] or 0.0})
            row.update({'price_unit': prod.wholesale_standard_price or 0.0})
            row.update({'amount': row['suggested_qty'] * row['price_unit']})
            res_table.append(row)
            total_row.update({'quantity': total_row['quantity'] + row['quantity'],
                              'onhand': total_row['onhand'] + row['onhand'],
                              'suggested_qty': total_row['suggested_qty'] + row['suggested_qty'],
                              'amount': total_row['amount'] + row['amount']})

        ################################# ASSIGIN FOR REPORT #################################
        self.get_lines = res_trans     # get_lines
        self.get_products = res_table
        self.get_total_row = total_row
        self.credit_limit = form['credit_limit'] or 0.0     # credit_limit
        self.credit_spent = top_row['row_total']
        self.credit_balance = self.credit_limit - self.credit_spent     # credit_balance
        self.suggested_po = total_row['amount']
        self.over_credit = self.suggested_po - self.credit_balance
        return True

    def _get_lines(self):
        return self.get_lines

    def _get_products(self):
        return self.get_products

    def _get_total_row(self):
        return self.get_total_row

    def _get_credit_limit(self):
        return self.credit_limit

    def _get_credit_spent(self):
        return self.credit_spent

    def _get_credit_balance(self):
        return self.credit_balance

    def _get_suggested_po(self):
        return self.suggested_po

    def _get_over_credit(self):
        return self.over_credit

    def _get_partners(self, data):
        partner_list = ''
        partner_obj = self.pool.get('res.partner')
        partner_ids = data['form']['partner_ids']
        for result in partner_obj.read(self.cr, self.uid, partner_ids, ['name']):
            partner_list += result['name'] + ', '
        return len(partner_list) > 1 and partner_list[:-2] or ''

report_sxw.report_sxw('report.daily_over_credit_limit', 'res.partner',
        'addons/report_daily_over_credit_limit/report/report_daily_over_credit_limit.rml', parser=report_daily_over_credit_limit, header="internal landscape")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
