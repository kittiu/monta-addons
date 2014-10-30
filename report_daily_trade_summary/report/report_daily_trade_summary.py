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
from openerp.report import report_sxw
from dateutil.relativedelta import relativedelta


class report_daily_trade_summary(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_daily_trade_summary, self).__init__(cr, uid, name, context=context)
        self.get_main_table = []
        self.get_summary_table = []
        self.get_total_table = []
        self.get_report_date = False
        self.get_purchase_cash = 0.0
        self.get_sale_cash = 0.0
        self.get_num_invoice = 0
        self.get_num_invoice_cancel = 0
        self.localcontext.update({
            'time': time,
            'init_data': self._init_data,
            'get_report_date': self._get_report_date,
            'get_main_table': self._get_main_table,
            'get_summary_table': self._get_summary_table,
            'get_total_table': self._get_total_table,
            'get_purchase_cash': self._get_purchase_cash,
            'get_sale_cash': self._get_sale_cash,
            'get_num_invoice': self._get_num_invoice,
            'get_num_invoice_cancel': self._get_num_invoice_cancel,
        })

    def _init_data(self, form):

        PURCHASE_QUERY = """
            select id, name, sum(quantity) as quantity,
                sum(discount * sign) as discount,
                sum(price_value * sign) as price_value,
                sum(cost_value * sign) as cost_value,
                sum((price_value - cost_value) * sign) as diff
            from (select pp.id, pp.name_template as name, quantity,
                (wholesale_unit_discount * quantity) as discount,
                (quantity * pp.wholesale_list_price) price_value,
                (quantity * pp.wholesale_standard_price) cost_value,
                (case when type='in_invoice' then 1 else -1 end) sign
                from account_invoice ai join account_invoice_line ail on ai.id = ail.invoice_id
                and ai.state != 'cancel'
                and ai.is_cigarette = true
                DATE_INVOICE_CONDITION
                PAYMENT_TERM_CONDITION
                join product_product pp on pp.id = ail.product_id
                where type in ('in_refund', 'in_invoice')) a
            group by id, name
        """
        SALE_QUERY = """
            select id, name, sum(quantity) as quantity,
                sum(discount * sign) as discount,
                sum(price_value * sign) as price_value,
                sum(cost_value * sign) as cost_value,
                sum((price_value - cost_value) * sign) as diff
            from (select pp.id, pp.name_template as name, quantity,
                (wholesale_unit_discount * quantity) as discount,
                (quantity * pp.wholesale_list_price) price_value,
                (quantity * pp.wholesale_standard_price) cost_value,
                (case when type='out_invoice' then 1 else -1 end) sign
                from account_invoice ai join account_invoice_line ail on ai.id = ail.invoice_id
                and ai.state != 'cancel'
                and ai.is_cigarette = true
                DATE_INVOICE_CONDITION
                PAYMENT_TERM_CONDITION
                join product_product pp on pp.id = ail.product_id
                where type in ('out_refund', 'out_invoice')) a
            group by id, name
        """

        blank_row = {
            'id': False,
            'name': False,
            'qty_purchase': False,
            'qty_purchase_price': False,
            'qty_purchase_cost': False,
            'qty_purchase_diff': False,
            'qty_sale': False,
            'qty_sale_price': False,
            'qty_sale_cost': False,
            'qty_sale_diff': False,
            'qty_onhand': False,
            'qty_onhand_price': False,
            'qty_onhand_cost': False,
            'qty_onhand_diff': False
        }
        report_date = form['date']
        first_date = time.strftime('%Y-%m-1')
        main_table = []  # Main table
        summary_table = []  # Summary Table
        row_summary = blank_row.copy()
        row_summary.update({'name': 'SUMMARY'})
        row_discount = blank_row.copy()
        row_discount.update({'name': u'ส่วนลดสะสม'})
        row_net_summary = blank_row.copy()
        row_net_summary.update({'name': 'NET SUMMARY'})
        total_table = []  # Total Table
        tot_summary = blank_row.copy()
        tot_summary.update({'name': u'ยอดรวมสะสม'})
        tot_discount = blank_row.copy()
        tot_discount.update({'name': u'ส่วนลดสะสม'})
        tot_net_summary = blank_row.copy()
        tot_net_summary.update({'name': u'คงเหลือสะสม'})

        ################################# Main Table (& Summary Table) #################################
        # Sales Product List
        query = """
            select pp.id, name
            from product_product pp, product_template pt
            where pp.product_tmpl_id = pt.id and sale_ok = true
            and pp.active = true
            order by id
        """
        self.cr.execute(query)
        res = self.cr.dictfetchall()
        for row in res:
            main_table.append({'id': row['id'],
                                'name': row['name'],
                                'qty_purchase': 0.0,
                                'qty_purchase_price': 0.0,
                                'qty_purchase_cost': 0.0,
                                'qty_purchase_diff': 0.0,
                                'qty_sale': 0.0,
                                'qty_sale_price': 0.0,
                                'qty_sale_cost': 0.0,
                                'qty_sale_diff': 0.0,
                                'qty_onhand': 0.0,
                                'qty_onhand_price': 0.0,
                                'qty_onhand_cost': 0.0,
                                'qty_onhand_diff': 0.0})
        # Purchase
        query = PURCHASE_QUERY.replace('DATE_INVOICE_CONDITION', 'and ai.date_invoice = %s').replace('PAYMENT_TERM_CONDITION', '')  # No Payment Term
        self.cr.execute(query, (report_date,))
        res = self.cr.dictfetchall()
        for row in res:
            for record in main_table:
                if record['id'] == row['id']:
                    record.update({'qty_purchase': row['quantity'],
                                            'qty_purchase_price': row['price_value'],
                                            'qty_purchase_cost': row['cost_value'],
                                            'qty_purchase_diff': row['diff']})
                    # SUMMARY
                    row_summary.update({'qty_purchase': row_summary['qty_purchase'] + row['quantity'],
                                        'qty_purchase_price': row_summary['qty_purchase_price'] + row['price_value'],
                                        'qty_purchase_cost': row_summary['qty_purchase_cost'] + row['cost_value'],
                                        'qty_purchase_diff': row_summary['qty_purchase_diff'] + row['diff']})
                    # Discount
                    row_discount.update({'qty_purchase_price': row_discount['qty_purchase_price'] + row['discount'],
                                         'qty_purchase_diff': row_discount['qty_purchase_diff'] + row['discount']})
        # Sale
        query = SALE_QUERY.replace('DATE_INVOICE_CONDITION', 'and ai.date_invoice = %s').replace('PAYMENT_TERM_CONDITION', '')  # No Payment Term
        self.cr.execute(query, (report_date,))
        res = self.cr.dictfetchall()
        for row in res:
            for record in main_table:
                if record['id'] == row['id']:
                    record.update({'qty_sale': row['quantity'],
                                            'qty_sale_price': row['price_value'],
                                            'qty_sale_cost': row['cost_value'],
                                            'qty_sale_diff': row['diff']})
                    # SUMMARY
                    row_summary.update({'qty_sale': row_summary['qty_sale'] + row['quantity'],
                                        'qty_sale_price': row_summary['qty_sale_price'] + row['price_value'],
                                        'qty_sale_cost': row_summary['qty_sale_cost'] + row['cost_value'],
                                        'qty_sale_diff': row_summary['qty_sale_diff'] + row['diff']})
                    # Discount
                    row_discount.update({'qty_sale_price': row_discount['qty_sale_price'] + row['discount'],
                                         'qty_sale_diff': row_discount['qty_sale_diff'] + row['discount']})
        # Onhand
        for row in main_table:
            product = self.pool.get('product.product').browse(self.cr, self.uid, row['id'])
            if row['id'] == product.id:
                qty_availables = self.pool.get('product.product').get_product_available(self.cr, self.uid, [product.id], context={'states': ('done',), 'what': ('in', 'out'), 'to_date': report_date + ' 23:59:59'})
                row.update({'qty_onhand': qty_availables[product.id] or 0.0,
                                        'qty_onhand_price': qty_availables[product.id] * product.wholesale_list_price or 0.0,
                                        'qty_onhand_cost': qty_availables[product.id] * product.wholesale_standard_price or 0.0,
                                        'qty_onhand_diff': (qty_availables[product.id] * product.wholesale_list_price) - (qty_availables[product.id] * product.wholesale_standard_price)})
                # SUMMARY
                row_summary.update({'qty_onhand': row_summary['qty_onhand'] + row['qty_onhand'],
                                    'qty_onhand_price': row_summary['qty_onhand_price'] + row['qty_onhand_price'],
                                    'qty_onhand_cost': row_summary['qty_onhand_cost'] + row['qty_onhand_cost'],
                                    'qty_onhand_diff': row_summary['qty_onhand_diff'] + row['qty_onhand_diff']})
        # Add summary records
        summary_table.append(row_summary)
        summary_table.append(row_discount)
        row_net_summary.update({
            'qty_purchase': row_summary['qty_purchase'] - row_discount['qty_purchase'],
            'qty_purchase_price': row_summary['qty_purchase_price'] - row_discount['qty_purchase_price'],
            'qty_purchase_cost': row_summary['qty_purchase_cost'] - row_discount['qty_purchase_cost'],
            'qty_purchase_diff': row_summary['qty_purchase_diff'] - row_discount['qty_purchase_diff'],
            'qty_sale': row_summary['qty_sale'] - row_discount['qty_sale'],
            'qty_sale_price': row_summary['qty_sale_price'] - row_discount['qty_sale_price'],
            'qty_sale_cost': row_summary['qty_sale_cost'] - row_discount['qty_sale_cost'],
            'qty_sale_diff': row_summary['qty_sale_diff'] - row_discount['qty_sale_diff'],
            'qty_onhand': row_summary['qty_onhand'] - row_discount['qty_onhand'],
            'qty_onhand_price': row_summary['qty_onhand_price'] - row_discount['qty_onhand_price'],
            'qty_onhand_cost': row_summary['qty_onhand_cost'] - row_discount['qty_onhand_cost'],
            'qty_onhand_diff': row_summary['qty_onhand_diff'] - row_discount['qty_onhand_diff']})
        summary_table.append(row_net_summary)

        ################################# TOTAL TABLE (bottom most) #################################
        # Purchase
        query = PURCHASE_QUERY.replace('DATE_INVOICE_CONDITION', 'and ai.date_invoice <= %s and ai.date_invoice >= %s').replace('PAYMENT_TERM_CONDITION', '')  # No Payment Term
        self.cr.execute(query, (report_date, first_date))
        res = self.cr.dictfetchall()
        for row in res:
            tot_summary.update({'qty_purchase': tot_summary['qty_purchase'] + row['quantity'],
                                        'qty_purchase_price': tot_summary['qty_purchase_price'] + row['price_value'],
                                        'qty_purchase_cost': tot_summary['qty_purchase_cost'] + row['cost_value'],
                                        'qty_purchase_diff': tot_summary['qty_purchase_diff'] + row['diff']})
            tot_discount.update({'qty_purchase_price': tot_discount['qty_purchase_price'] + row['discount'],
                                 'qty_purchase_diff': tot_discount['qty_purchase_diff'] + row['discount']})
        # Sale
        query = SALE_QUERY.replace('DATE_INVOICE_CONDITION', 'and ai.date_invoice <= %s and ai.date_invoice >= %s').replace('PAYMENT_TERM_CONDITION', '')  # No Payment Term
        self.cr.execute(query, (report_date, first_date))
        res = self.cr.dictfetchall()
        for row in res:
            tot_summary.update({'qty_sale': tot_summary['qty_sale'] + row['quantity'],
                                        'qty_sale_price': tot_summary['qty_sale_price'] + row['price_value'],
                                        'qty_sale_cost': tot_summary['qty_sale_cost'] + row['cost_value'],
                                        'qty_sale_diff': tot_summary['qty_sale_diff'] + row['diff']})
            tot_discount.update({'qty_sale_price': tot_discount['qty_sale_price'] + row['discount'],
                                 'qty_sale_diff': tot_discount['qty_sale_diff'] + row['discount']})
        # Add summary records
        total_table.append(tot_summary)
        total_table.append(tot_discount)
        tot_net_summary.update({
            'qty_purchase': tot_summary['qty_purchase'] - tot_discount['qty_purchase'],
            'qty_purchase_price': tot_summary['qty_purchase_price'] - tot_discount['qty_purchase_price'],
            'qty_purchase_cost': tot_summary['qty_purchase_cost'] - tot_discount['qty_purchase_cost'],
            'qty_purchase_diff': tot_summary['qty_purchase_diff'] - tot_discount['qty_purchase_diff'],
            'qty_sale': tot_summary['qty_sale'] - tot_discount['qty_sale'],
            'qty_sale_price': tot_summary['qty_sale_price'] - tot_discount['qty_sale_price'],
            'qty_sale_cost': tot_summary['qty_sale_cost'] - tot_discount['qty_sale_cost'],
            'qty_sale_diff': tot_summary['qty_sale_diff'] - tot_discount['qty_sale_diff']})
        total_table.append(tot_net_summary)

        ################################# Today Cash (bottom line) #################################
        # Purchase
        query = PURCHASE_QUERY.replace('DATE_INVOICE_CONDITION', 'and ai.date_invoice = %s').replace('PAYMENT_TERM_CONDITION', 'and ai.payment_term = 1')  # Cash
        self.cr.execute(query, (report_date,))
        res = self.cr.dictfetchall()
        purchase_cash = 0.0
        for row in res:
            purchase_cash += row['cost_value']
        # Sale, getting from payment_register
        query = """
            select sum(amount) amount_payin from payment_register
            where state not in ('cancel','bounce_check') and type = 'cash' and date = %s
        """
        self.cr.execute(query, (report_date,))
        res = self.cr.dictfetchone()
        sale_cash = res['amount_payin'] or 0.0
        ################################# Number of Invoice #################################
        query = """
            select (select count(*) from account_invoice
            where state != 'draft' and type = 'out_invoice' and date_invoice = %s) as num_invoice,
            (select count(*) from account_invoice
            where state = 'cancel' and type = 'out_invoice' and date_invoice = %s) as num_invoice_cancel
        """
        self.cr.execute(query, (report_date, report_date))
        res = self.cr.dictfetchone()
        num_invoice = res['num_invoice']
        num_invoice_cancel = res['num_invoice_cancel']

        ################################# ASSIGIN FOR REPORT #################################
        report_date = datetime.strptime(form['date'], '%Y-%m-%d')
        self.get_report_date = 'ประจำวันที่ ' + str(report_date.day) + ' ' + self._get_month(report_date.month) + ' ' + 'พ.ศ. ' + str(report_date.year + 543)
        self.get_main_table = main_table
        self.get_summary_table = summary_table
        self.get_total_table = total_table
        self.get_purchase_cash = purchase_cash
        self.get_sale_cash = sale_cash
        self.get_num_invoice = num_invoice
        self.get_num_invoice_cancel = num_invoice_cancel
        return True

    def _get_report_date(self):
        return self.get_report_date

    def _get_main_table(self):
        return self.get_main_table

    def _get_summary_table(self):
        return self.get_summary_table

    def _get_total_table(self):
        return self.get_total_table

    def _get_purchase_cash(self):
        return self.get_purchase_cash

    def _get_sale_cash(self):
        return self.get_sale_cash

    def _get_num_invoice(self):
        return self.get_num_invoice

    def _get_num_invoice_cancel(self):
        return self.get_num_invoice_cancel

    def _get_month(self, month):
        months = {1: u'มกราคม',
                  2: u'กุมภาพันธ์',
                  3: u'มีนาคม',
                  4: u'เมษายน',
                  5: u'พฤษภาคม',
                  6: u'มิถุนายน',
                  7: u'กรกฏาคม',
                  8: u'สิงหาคม',
                  9: u'กันยายน',
                  10: u'ตุลาคม',
                  11: u'พฤษจิกายน',
                  12: u'ธันวาคม',
                  }
        return months[month]

report_sxw.report_sxw('report.daily_trade_summary', 'res.partner',
        'addons/report_daily_trade_summary/report/report_daily_trade_summary.rml', parser=report_daily_trade_summary, header="internal landscape")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
