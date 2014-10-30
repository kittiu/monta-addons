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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import types


class account_invoice(osv.osv):

    # Method override
    def _amount_all(self, cr, uid, ids, name, args, context=None):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                # Wholesale
                'wholesale_amount_untaxed': 0.0,
                'wholesale_amount_tax': 0.0,
                'wholesale_amount_total': 0.0,
                'wholesale_discount': 0.0,
                'wholesale_balance': 0.0,
                # Retail
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0
            }
            cur = invoice.currency_id
            # Original as Retail
            for line in invoice.invoice_line:
                res[invoice.id]['amount_untaxed'] += line.price_subtotal
            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount
            res[invoice.id]['amount_total'] = res[invoice.id]['amount_tax'] + res[invoice.id]['amount_untaxed']
            # Wholesale Amount
            if not invoice.is_price_included_tax:
                val_discount = 0.0
                for line in invoice.wholesale_invoice_line:
                    res[invoice.id]['wholesale_amount_untaxed'] += line.wholesale_price_subtotal
                    val_discount += line.wholesale_unit_discount * line.quantity
                res[invoice.id]['wholesale_amount_tax'] = res[invoice.id]['amount_tax']
                res[invoice.id]['wholesale_amount_total'] = res[invoice.id]['wholesale_amount_untaxed'] + res[invoice.id]['wholesale_amount_tax']
                res[invoice.id]['wholesale_discount'] = cur_obj.round(cr, uid, cur, val_discount)
                res[invoice.id]['wholesale_balance'] = res[invoice.id]['wholesale_amount_total'] - res[invoice.id]['wholesale_discount']
            else:
                val_total = 0.0
                val_discount = 0.0
                for line in invoice.wholesale_invoice_line:
                    wholesale_price = line.wholesale_price_unit - line.wholesale_unit_discount
                    val_total += wholesale_price * line.quantity
                    val_discount += line.wholesale_unit_discount * line.quantity
                res[invoice.id]['wholesale_balance'] = cur_obj.round(cr, uid, cur, val_total)
                res[invoice.id]['wholesale_discount'] = cur_obj.round(cr, uid, cur, val_discount)
                res[invoice.id]['wholesale_amount_total'] = res[invoice.id]['wholesale_balance'] + res[invoice.id]['wholesale_discount']
                res[invoice.id]['wholesale_amount_tax'] = res[invoice.id]['amount_tax']
                res[invoice.id]['wholesale_amount_untaxed'] = res[invoice.id]['wholesale_amount_total'] - res[invoice.id]['wholesale_amount_tax']
        return res

    # Method override
    def _get_invoice_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    # Method override
    def _get_invoice_tax(self, cr, uid, ids, context=None):
        result = {}
        for tax in self.pool.get('account.invoice.tax').browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    def _is_price_included_tax(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            price_include_list = []
            res[invoice.id] = False
            for line in invoice.invoice_line:
                if line.invoice_line_tax_id:
                    for tax in line.invoice_line_tax_id:
                        price_include_list += [tax.price_include or False]
                else:
                    price_include_list += [False]
            price_include_list = list(set(price_include_list))  # Get unique values of price_include
            if price_include_list:
                if len(price_include_list) > 1:
                    raise osv.except_osv(_('Tax Included in Price Exception!'),
                        _('Mixing between tax included in price and not included in price!'))
                else:
                    res[invoice.id] = price_include_list[0]
        return res

    _inherit = 'account.invoice'
    _columns = {
        'is_cigarette': fields.boolean('Cigarette'),
        'is_price_included_tax': fields.function(_is_price_included_tax, store=False, string='Tax Included in Price', type='boolean'),
        'wholesale_invoice_line': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=True, states={'draft': [('readonly', False)]}),
        # Wholesale Amount
        'wholesale_amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'wholesale_amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'wholesale_amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Wholesale Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'wholesale_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discount',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'wholesale_balance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Balance',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        # Retail Amount
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Subtotal', track_visibility='always',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Tax',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Retail Total',
            store={
                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_invoice_line', 'invoice_line'], 20),
                'account.invoice.tax': (_get_invoice_tax, None, 20),
                'account.invoice.line': (_get_invoice_line, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'invoice_line_tax_id', 'quantity', 'discount', 'invoice_id'], 20),
            },
            multi='all'),

    }
    _defaults = {
        'is_cigarette': True,
    }

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        move_lines = super(account_invoice, self).finalize_invoice_move_lines(cr, uid, invoice_browse, move_lines)
        return move_lines
    
    def create(self, cr, uid, data, context=None):
        result = super(account_invoice, self).create(cr, uid, data, context=context)
        self.button_reset_taxes(cr, uid, [result], context)
        return result

    # Method override -- if date_due is already assigned. Use that date.
    def action_date_assign(self, cr, uid, ids, *args):
        for inv in self.browse(cr, uid, ids):
            res = self.onchange_payment_term_date_invoice(cr, uid, inv.id, inv.payment_term.id, inv.date_invoice)
            if res and res['value']:
                if not inv.date_due: # kittiu
                    self.write(cr, uid, [inv.id], res['value'])
        return True
    
    # Method override -- if date_due is already assigned. Use that date.
    def action_move_create(self, cr, uid, ids, context=None):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        period_obj = self.pool.get('account.period')
        payment_term_obj = self.pool.get('account.payment.term')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': fields.date.context_today(self,cr,uid,context=context)}, context=ctx)
            company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
            # create the analytical lines
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id, context=ctx)
            # check if taxes are all computed
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=ctx)
            self.check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)

            # I disabled the check_total feature
            group_check_total_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account', 'group_supplier_inv_check_total')[1]
            group_check_total = self.pool.get('res.groups').browse(cr, uid, group_check_total_id, context=context)
            if group_check_total and uid in [x.id for x in group_check_total.users]:
                if (inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0)):
                    raise osv.except_osv(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))

            if inv.payment_term:
                total_fixed = total_percent = 0
                for line in inv.payment_term.line_ids:
                    if line.value == 'fixed':
                        total_fixed += line.value_amount
                    if line.value == 'procent':
                        total_percent += line.value_amount
                total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
                if (total_fixed + total_percent) > 100:
                    raise osv.except_osv(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            entry_type = ''
            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
                entry_type = 'journal_pur_voucher'
                if inv.type == 'in_refund':
                    entry_type = 'cont_voucher'
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                entry_type = 'journal_sale_vou'
                if inv.type == 'out_refund':
                    entry_type = 'cont_voucher'

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            total, total_currency, iml = self.compute_invoice_totals(cr, uid, inv, company_currency, ref, iml, context=ctx)
            acc_id = inv.account_id.id

            name = inv['name'] or inv['supplier_invoice_number'] or '/'
            totlines = False
            # kittiu
            #if inv.payment_term:
            if inv.payment_term and not inv.date_due:
            # --
                totlines = payment_term_obj.compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context=ctx)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                ctx.update({'date': inv.date_invoice})
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid, company_currency, inv.currency_id.id, t[1], context=ctx)
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity': inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')

            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part.id, date, context=ctx)),iml)

            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {
                'ref': inv.reference and inv.reference or inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            period_id = inv.period_id and inv.period_id.id or False
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            if not period_id:
                period_ids = period_obj.find(cr, uid, inv.date_invoice, context=ctx)
                period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            ctx.update(invoice=inv)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True

account_invoice()


class account_invoice_line(osv.osv):

    # Method override
    def _amount_line(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res = {}
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        for line in self.browse(cr, uid, ids):
            res[line.id] = {
                'wholesale_price_subtotal': 0.0,
                'price_subtotal': 0.0,
            }
            # Original as Retail
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
            res[line.id]['price_subtotal'] = taxes['total']
            if line.invoice_id:
                cur = line.invoice_id.currency_id
                res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, res[line.id]['price_subtotal'])
                # Wholesale
                wholesale_price = line.wholesale_price_unit - line.wholesale_unit_discount
                wholesale_taxes = tax_obj.compute_all(cr, uid, line.invoice_line_tax_id, wholesale_price, line.quantity, product=line.product_id, partner=line.invoice_id.partner_id)
                res[line.id]['wholesale_price_subtotal'] = cur_obj.round(cr, uid, cur, wholesale_taxes['total'])
        return res

    _inherit = 'account.invoice.line'
    _columns = {
        'wholesale_price_unit': fields.float('Wholesale Unit Price', required=True, digits_compute=dp.get_precision('Product Price')),
        'wholesale_unit_discount': fields.float('Wholesale Unit Discount', required=True, digits_compute=dp.get_precision('Discount')),
        'wholesale_price_subtotal': fields.function(_amount_line, string='Wholesale Amount', type="float",
            digits_compute=dp.get_precision('Account'), store=True, multi='line'),
        'price_subtotal': fields.function(_amount_line, string='Amount', type="float",
            digits_compute=dp.get_precision('Account'), store=True, multi='line'),
        'wholesale_price_unit_readonly': fields.related('wholesale_price_unit', string='Wholesale Unit Price', readonly=True),
        'price_unit_readonly': fields.related('price_unit', string='Unit Price', readonly=True),
    }

    def product_id_change(self, cr, uid, ids, product, uom_id, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, currency_id=False, context=None, company_id=None):
        res_final = super(account_invoice_line, self).product_id_change(cr, uid, ids, product, uom_id, qty, name, type, partner_id, fposition_id, price_unit, currency_id=currency_id, context=context, company_id=company_id)
        if res_final.get('value', False):
            res = self.pool.get('product.product').browse(cr, uid, product, context=context)
            if type in ('in_invoice', 'in_refund'):
                res_final['value'].update({'wholesale_price_unit': res.wholesale_standard_price})
            else:
                res_final['value'].update({'wholesale_price_unit': res.wholesale_list_price})
        return res_final

    def _add_moveline_wholesale_discount(self, cr, uid, inv, res, context=None):
        if inv.is_cigarette and inv.wholesale_discount > 0.0:
            sign = -1
            #sign = inv.type in ('out_invoice','in_invoice') and -1 or 1
            # account code for advance
            prop = inv.type in ('out_invoice', 'out_refund') \
                        and self.pool.get('ir.property').get(cr, uid, 'property_account_wholesale_disc_customer', 'res.partner', context=context) \
                        or self.pool.get('ir.property').get(cr, uid, 'property_account_wholesale_disc_supplier', 'res.partner', context=context)
            prop_id = prop and prop.id or False
            if not prop_id:
                raise osv.except_osv(_('Error Accounting!'),
                    _('Account for Wholesale Discount is not set!'))
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False, prop_id)

            res.append({
                'type': 'src',
                'name': _('Additional Discount'),
                'price_unit': sign * inv.wholesale_discount,
                'quantity': 1,
                'price': sign * inv.wholesale_discount,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })
        return res

    def _add_account_rounding(self, cr, uid, inv, res, context=None):
        if inv.is_cigarette:
            sign = -1
            diff = sum([i['price'] for i in res]) - inv.wholesale_amount_untaxed
            if diff:
                prop = self.pool.get('ir.property').get(cr, uid, 'property_account_journal_rounding', 'account.journal', context=context)
                prop_id = prop and prop.id or False
                if not prop_id:
                    raise osv.except_osv(_('Error Accounting!'),
                        _('Account for Amount Rounding is not set!'))
                account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False, prop_id)
                res.append({
                    'type': 'src',
                    'name': _('Accounting Rounding'),
                    'price_unit': sign * diff,
                    'quantity': 1,
                    'price': sign * diff,
                    'account_id': account_id,
                    'product_id': False,
                    'uos_id': False,
                    'account_analytic_id': False,
                    'taxes': False,
                })
        return res

    def move_line_get(self, cr, uid, invoice_id, context=None):
        if context == None:
            context = {}
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        if inv.is_cigarette:
            context.update({'is_cigarette': True})
        res = super(account_invoice_line, self).move_line_get(cr, uid, invoice_id, context=context)

        res = self._add_account_rounding(cr, uid, inv, res, context=context)
        res = self._add_moveline_wholesale_discount(cr, uid, inv, res, context=context)

        return res

    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(account_invoice_line, self).move_line_get_item(cr, uid, line, context=context)
        if 'is_cigarette' in context and context['is_cigarette']:
            cur_obj = self.pool.get('res.currency')
            cur = line.invoice_id.currency_id
            if line.invoice_id.type in ('in_invoice', 'in_refund'):
                res['price_unit'] = line.product_id.wholesale_standard_price - line.product_id.purchase_vat
            else:
                res['price_unit'] = line.product_id.wholesale_list_price - line.product_id.sale_vat
            res['price'] = cur_obj.round(cr, uid, cur, line.quantity * res['price_unit'])
        return res

account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
