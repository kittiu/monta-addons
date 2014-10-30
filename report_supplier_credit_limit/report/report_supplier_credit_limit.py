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
from openerp import pooler

# Query to calculate current stock value, from report_stock_inventory view, but change standard_price to whole_sale_standard_price
REPORT_STOCK_INVENTORY_QUERY = """
select sum(value) stock_value
from (
         SELECT min(m.id) AS id, m.date, to_char(m.date, 'YYYY'::text) AS year, to_char(m.date, 'MM'::text) AS month, m.partner_id, m.location_id, m.product_id, pt.categ_id AS product_categ_id, l.usage AS location_type, l.scrap_location, m.company_id, m.state, m.prodlot_id, COALESCE(sum((- pp.wholesale_standard_price) * m.product_qty * pu.factor / pu2.factor), 0.0) AS value, COALESCE(sum((- m.product_qty) * pu.factor / pu2.factor), 0.0) AS product_qty
           FROM stock_move m
      LEFT JOIN stock_picking p ON m.picking_id = p.id
   LEFT JOIN product_product pp ON m.product_id = pp.id
   LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
   LEFT JOIN product_uom pu ON pt.uom_id = pu.id
   LEFT JOIN product_uom pu2 ON m.product_uom = pu2.id
   LEFT JOIN product_uom u ON m.product_uom = u.id
   LEFT JOIN stock_location l ON m.location_id = l.id
  WHERE m.state::text <> 'cancel'::text
  GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, m.location_dest_id, m.prodlot_id, m.date, m.state, l.usage, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'::text), to_char(m.date, 'MM'::text)
UNION ALL
         SELECT - m.id AS id, m.date, to_char(m.date, 'YYYY'::text) AS year, to_char(m.date, 'MM'::text) AS month, m.partner_id, m.location_dest_id AS location_id, m.product_id, pt.categ_id AS product_categ_id, l.usage AS location_type, l.scrap_location, m.company_id, m.state, m.prodlot_id, COALESCE(sum(pp.wholesale_standard_price * m.product_qty * pu.factor / pu2.factor), 0.0) AS value, COALESCE(sum(m.product_qty * pu.factor / pu2.factor), 0.0) AS product_qty
           FROM stock_move m
      LEFT JOIN stock_picking p ON m.picking_id = p.id
   LEFT JOIN product_product pp ON m.product_id = pp.id
   LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
   LEFT JOIN product_uom pu ON pt.uom_id = pu.id
   LEFT JOIN product_uom pu2 ON m.product_uom = pu2.id
   LEFT JOIN product_uom u ON m.product_uom = u.id
   LEFT JOIN stock_location l ON m.location_dest_id = l.id
  WHERE m.state::text <> 'cancel'::text
  GROUP BY m.id, m.product_id, m.product_uom, pt.categ_id, m.partner_id, m.location_id, m.location_dest_id, m.prodlot_id, m.date, m.state, l.usage, l.scrap_location, m.company_id, pt.uom_id, to_char(m.date, 'YYYY'::text), to_char(m.date, 'MM'::text)
) a

where location_type = 'internal' and state = 'done';
"""


class report_supplier_credit_limit(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_supplier_credit_limit, self).__init__(cr, uid, name, context=context)
        self.get_lines = []
        self.credit_limit = 0.0
        self.credit_spent = 0.0
        self.credit_balance = 0.0
        self.future_balance = {}
        self.po_line = {}
        self.stock_value_line = {}
        self.over_credit = {}
        self.localcontext.update({
            'time': time,
            'init_data': self._init_data,
            'get_lines': self._get_lines,
            'get_credit_limit': self._get_credit_limit,
            'get_credit_spent': self._get_credit_spent,
            'get_credit_balance': self._get_credit_balance,
            'get_future_balance': self._get_future_balance,
            'get_po_line': self._get_po_line,
            'get_stock_value_line': self._get_stock_value_line,
            'get_over_credit': self._get_over_credit,
            'get_partners': self._get_partners,
        })

    def _init_data(self, form):

        partner_obj = self.pool.get('res.partner')
        partner_ids = form['partner_ids']

        ################################# DATA FROM SUPPLIER INVOICE #################################
        inv_type = ['in_invoice']
        state = ['open']
        partner_names = {}
        query = "select id, name, total from \
                (select partner.id, partner.name, sum(coalesce(ai.wholesale_balance, 0)) total from res_partner partner \
                left outer join account_invoice ai on partner.id = ai.partner_id \
                and ai.type in %s and ai.state in %s and \
                REPLACE_CONDITION \
                where partner.id in %s \
                group by partner.id, partner.name) a \
                order by name"

        res = {}
        date_total = {}
        # Get total undue amount for each partner (after 7th date)
        self.cr.execute(query.replace('REPLACE_CONDITION', 'ai.date_due > %s'), (tuple(inv_type), tuple(state), form['6']['date_to'], tuple(partner_ids)))
        res.update({'undue': {}})
        date_total.update({'undue': 0.0})
        partners = self.cr.dictfetchall()
        for partner in partners:
            res['undue'].update({partner['id']: {'total': partner['total']}})
            date_total.update({'undue': date_total['undue'] + partner['total']})

        # Get total previous due amount for each partner (before 1st date)
        self.cr.execute(query.replace('REPLACE_CONDITION', 'ai.date_due < %s'), (tuple(inv_type), tuple(state), form['date_from'], tuple(partner_ids)))
        res.update({'prevdue': {}})
        date_total.update({'prevdue': 0.0})
        partners = self.cr.dictfetchall()
        for partner in partners:
            res['prevdue'].update({partner['id']: {'total': partner['total']}})
            date_total.update({'prevdue': date_total['prevdue'] + partner['total']})

        # Get total for each partner for given date(i)
        for i in range(7):
            date_total.update({str(i): 0.0})
            res.update({str(i): {}})
            self.cr.execute(query.replace('REPLACE_CONDITION', 'ai.date_due between %s and %s'), (tuple(inv_type), tuple(state), form[str(i)]['date_from'], form[str(i)]['date_to'] + ' 24:00:00', tuple(partner_ids)))
            partners = self.cr.dictfetchall()
            for partner in partners:
                if i == 0:
                    partner_names.update({partner['id']: partner['name']})
                res[str(i)].update({partner['id']: {'total': partner['total']}})
                # Total of each date (column_total)
                date_total.update({str(i): date_total[str(i)] + partner['total']})

        # Transform to list
        res_trans = []
        top_row = {'id': 0, 'name': 'Period Total'}  # Prepare total amount as first row
        top_row_total = 0.0
        for partner_id in partner_ids:  # For normal rows
            row = {'id': partner_id, 'name': partner_names[partner_id]}
            row_total = 0.0
            for i in range(7):
                cell_total = res[str(i)][partner_id]['total']
                row_total += cell_total
                row.update({str(i): cell_total})

            row.update({'undue': res['undue'][partner_id]['total'],
                        'prevdue': res['prevdue'][partner_id]['total'],
                        'row_total': row_total + res['prevdue'][partner_id]['total'] + res['undue'][partner_id]['total']})  # Add row total
            res_trans.append(row)

        for i in range(7):  # For top_row only
            top_row.update({str(i): date_total[str(i)]})
            top_row_total += date_total[str(i)]
        top_row.update({'undue': date_total['undue'],
                        'prevdue': date_total['prevdue'],
                        'row_total': top_row_total + date_total['prevdue'] + date_total['undue']})

        res_trans.insert(0, top_row)  # Insert top row

        ################################# DATA FROM PURCHASE ORDER #################################
        state = ['draft']
        query = "select sum(wholesale_balance) total from purchase_order \
                where (state = 'draft' or (state in ('confirmed','approved') and shipped = False)) \
                and minimum_planned_date between %s and %s and partner_id in %s"
        po_row = {}
        date_total = {}
        row_total = 0.0
        # Get total for each partner for given date(i)
        for i in range(7):
            po_row.update({str(i): 0.0})
            self.cr.execute(query, (form[str(i)]['date_from'], form[str(i)]['date_to'] + ' 24:00:00', tuple(partner_ids)))
            total = self.cr.dictfetchall()[0]['total'] or 0.0
            po_row.update({str(i): total})
            row_total += total
        po_row.update({'undue': 0.0,
                       'row_total': row_total})

        ################################# DATA FROM STOCK VALUE #################################
        state = ['draft']
        query = REPORT_STOCK_INVENTORY_QUERY
        stock_value_row = {}
        date_total = {}
        total = 0.0
        self.cr.execute(query)
        total = self.cr.dictfetchall()[0]['stock_value'] or 0.0
        # Get total for each partner for given date(i)
        for i in range(7):
            stock_value_row.update({str(i): 0.0})
            stock_value_row.update({str(i): total})
        stock_value_row.update({'undue': 0.0,
                       'row_total': total})

        ################################# ASSIGIN FOR REPORT #################################
        self.get_lines = res_trans     # get_lines
        self.credit_limit = form['credit_limit'] or 0.0     # credit_limit
        # credit_spent from partner's total payable
        self.credit_spent = sum([res['debit'] for res in partner_obj.read(self.cr, self.uid, partner_ids, ['debit'])])
        self.credit_balance = self.credit_limit - self.credit_spent     # credit_balance
        for i in range(7):  # future_balance
            self.future_balance.update({str(i): top_row[str(i)] + self.credit_balance})
        self.future_balance.update({'undue': top_row['undue'] + self.credit_balance})
        self.po_line = po_row   # po_row
        self.stock_value_line = stock_value_row   # stock_value_row
        for i in range(7):  # over_credit
            self.over_credit.update({str(i): self.future_balance[str(i)] - self.po_line[str(i)] + self.stock_value_line[str(i)]})
        self.over_credit.update({'undue': self.future_balance['undue'] - self.po_line['undue'] + - self.stock_value_line['undue'],
                                 'row_total': self.credit_balance + top_row['row_total'] - self.po_line['row_total'] + self.stock_value_line['row_total']})
        return True

    def _get_lines(self):
        return self.get_lines

    def _get_credit_limit(self):
        return self.credit_limit

    def _get_credit_spent(self):
        return self.credit_spent

    def _get_credit_balance(self):
        return self.credit_balance

    def _get_future_balance(self, i):
        return self.future_balance[i]

    def _get_po_line(self, i):
        return self.po_line[i]

    def _get_stock_value_line(self, i):
        return self.stock_value_line[i]

    def _get_over_credit(self, i):
        return self.over_credit[i]

    def _get_partners(self, data):
        partner_list = ''
        partner_obj = self.pool.get('res.partner')
        partner_ids = data['form']['partner_ids']
        for result in partner_obj.read(self.cr, self.uid, partner_ids, ['name']):
            partner_list += result['name'] + ', '
        return len(partner_list) > 1 and partner_list[:-2] or ''

report_sxw.report_sxw('report.supplier_credit_limit', 'res.partner',
        'addons/report_supplier_credit_limit/report/report_supplier_credit_limit.rml', parser=report_supplier_credit_limit, header="internal landscape")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
