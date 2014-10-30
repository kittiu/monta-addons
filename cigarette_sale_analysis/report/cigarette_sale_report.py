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

from openerp import tools
from openerp.osv import fields,osv

class cigarette_sale_report(osv.osv):
    _name = "cigarette.sale.report"
    _description = "Cigarette Sales Statistics"
    _auto = False
    _rec_name = 'date'

    _columns = {
        'date': fields.date('Date', readonly=True),
        'year': fields.char('Year', size=4, readonly=True),
        'day': fields.char('Day', size=128, readonly=True),
        'month': fields.selection([('01','January'), ('02','February'), ('03','March'), ('04','April'),
            ('05','May'), ('06','June'), ('07','July'), ('08','August'), ('09','September'),
            ('10','October'), ('11','November'), ('12','December')], 'Month', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'product_qty':fields.float('Qty', readonly=True),
        'uom_name': fields.char('Reference Unit of Measure', size=128, readonly=True),
        'payment_term': fields.many2one('account.payment.term', 'Payment Term', readonly=True),
        'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], readonly=True),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position', readonly=True),
        'categ_id': fields.many2one('product.category','Category of Product', readonly=True),
        'journal_id': fields.many2one('account.journal', 'Journal', readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        'modern_trade': fields.boolean('Modern Trade', readonly=True),
        'traditional_trade': fields.boolean('Traditional Trade', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', readonly=True),
        'user_id': fields.many2one('res.users', 'Salesperson', readonly=True),
        'price_total': fields.float('Sales', readonly=True),
        'price_cost': fields.float('Cost', readonly=True),
        'price_margin': fields.float('Margin', readonly=True),
        'nbr':fields.integer('# of Lines', readonly=True),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', readonly=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Done'),
            ('cancel','Cancelled')
            ], 'Invoice Status', readonly=True),
        'date_due': fields.date('Due Date', readonly=True),
        'account_id': fields.many2one('account.account', 'Account',readonly=True),
        'account_line_id': fields.many2one('account.account', 'Account Line',readonly=True),
        'partner_bank_id': fields.many2one('res.partner.bank', 'Bank Account',readonly=True),
    }
    _order = 'date desc'

    def init(self, cr):
        # self._table = cigarette_sale_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW cigarette_sale_report as (
 SELECT sub.id,
    sub.date,
    sub.year,
    sub.month,
    sub.day,
    sub.product_id,
    sub.partner_id,
      CASE
    WHEN (select count(*) from res_partner_res_partner_category_rel rel where sub.partner_id = rel.partner_id and rel.category_id = 1) > 0 
    THEN true 
    ELSE false 
      END as modern_trade,
      CASE
    WHEN (select count(*) from res_partner_res_partner_category_rel rel where sub.partner_id = rel.partner_id and rel.category_id = 2) > 0 
    THEN true 
    ELSE false 
      END as traditional_trade,
    sub.payment_term,
    sub.period_id,
    sub.uom_name,
    sub.journal_id,
    sub.fiscal_position,
    sub.user_id,
    sub.company_id,
    sub.nbr,
    sub.type,
    sub.state,
    sub.categ_id,
    sub.date_due,
    sub.account_id,
    sub.account_line_id,
    sub.partner_bank_id,
    sub.product_qty,
    (sub.product_qty * sub.unit_price) as price_total,
    (sub.product_qty * sub.cost_price) as price_cost,
    (sub.product_qty * sub.unit_price) - (sub.product_qty * sub.cost_price) as price_margin
   FROM ( SELECT min(ail.id) AS id,
            ai.date_invoice AS date,
            to_char(ai.date_invoice::timestamp with time zone, 'YYYY'::text) AS year,
            to_char(ai.date_invoice::timestamp with time zone, 'MM'::text) AS month,
            to_char(ai.date_invoice::timestamp with time zone, 'YYYY-MM-DD'::text) AS day,
            ail.product_id,
            (ail.wholesale_price_unit - ail.wholesale_unit_discount) as unit_price, --kittiu
            pr.wholesale_standard_price as cost_price, --kittiu
            ai.partner_id,
            ai.payment_term,
            ai.period_id,
                CASE
                    WHEN u.uom_type::text <> 'reference'::text THEN ( SELECT product_uom.name
                       FROM product_uom
                      WHERE product_uom.uom_type::text = 'reference'::text AND product_uom.active AND product_uom.category_id = u.category_id
                     LIMIT 1)
                    ELSE u.name
                END AS uom_name,
            ai.journal_id,
            ai.fiscal_position,
            ai.user_id,
            ai.company_id,
            count(ail.*) AS nbr,
            ai.type,
            ai.state,
            pt.categ_id,
            ai.date_due,
            ai.account_id,
            ail.account_id AS account_line_id,
            ai.partner_bank_id,
            sum(
                CASE
                    WHEN ai.type::text = ANY (ARRAY['out_refund'::character varying::text, 'in_invoice'::character varying::text]) THEN (- ail.quantity) / u.factor
                    ELSE ail.quantity / u.factor
                END) AS product_qty
           FROM account_invoice_line ail
      JOIN account_invoice ai ON ai.id = ail.invoice_id and ai.is_cigarette = true
   LEFT JOIN product_product pr ON pr.id = ail.product_id
   LEFT JOIN product_template pt ON pt.id = pr.product_tmpl_id
   LEFT JOIN product_uom u ON u.id = ail.uos_id
  GROUP BY ail.product_id, (ail.wholesale_price_unit - ail.wholesale_unit_discount), pr.wholesale_standard_price, ai.date_invoice, ai.id, to_char(ai.date_invoice::timestamp with time zone, 'YYYY'::text), to_char(ai.date_invoice::timestamp with time zone, 'MM'::text), to_char(ai.date_invoice::timestamp with time zone, 'YYYY-MM-DD'::text), ai.partner_id, ai.payment_term, ai.period_id, u.name, ai.journal_id, ai.fiscal_position, ai.user_id, ai.company_id, ai.type, ai.state, pt.categ_id, ai.date_due, ai.account_id, ail.account_id, ai.partner_bank_id, u.uom_type, u.category_id) sub
                        )""")

cigarette_sale_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
