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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class purchase_order(osv.osv):

    # Method override
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj = self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                # Wholesale
                'wholesale_amount_untaxed': 0.0,
                'wholesale_amount_tax': 0.0,
                'wholesale_amount_total': 0.0,
                'wholesale_discount': 0.0,
                'wholesale_balance': 0.0,
                # Original as retail
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            # Original as retail
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                for c in self.pool.get('account.tax').compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
            # Wholesale Amount
            cur = order.pricelist_id.currency_id
            # Case 1: tax not included, Sum(Subtotal) = Untaxed, then get Tax = Retail Tax to calculate total
            if not order.is_price_included_tax:
                val_untaxed = 0.0
                val_discount = 0.0
                for line in order.wholesale_order_line:
                    val_untaxed += line.wholesale_price_subtotal
                    val_discount += line.wholesale_unit_discount * line.product_qty
                res[order.id]['wholesale_amount_untaxed'] = cur_obj.round(cr, uid, cur, val_untaxed)
                res[order.id]['wholesale_amount_tax'] = res[order.id]['amount_tax']
                res[order.id]['wholesale_amount_total'] = res[order.id]['wholesale_amount_untaxed'] + res[order.id]['wholesale_amount_tax']
                res[order.id]['wholesale_discount'] = cur_obj.round(cr, uid, cur, val_discount)
                res[order.id]['wholesale_balance'] = res[order.id]['wholesale_amount_total'] - res[order.id]['wholesale_discount']
            # Case 2: tax included, Sum(Subtotal before tax deduction) = Total, then get Tax = Retail Tax to calculate Untaxed Amount
            else:
                val_total = 0.0
                val_discount = 0.0
                for line in order.wholesale_order_line:
                    # For Wholesales, require to replace price_subtotal again,
                    wholesale_price = line.wholesale_price_unit - line.wholesale_unit_discount
                    val_total += wholesale_price * line.product_qty
                    val_discount += line.wholesale_unit_discount * line.product_qty
                res[order.id]['wholesale_balance'] = cur_obj.round(cr, uid, cur, val_total)
                res[order.id]['wholesale_discount'] = cur_obj.round(cr, uid, cur, val_discount)
                res[order.id]['wholesale_amount_total'] = res[order.id]['wholesale_balance'] + res[order.id]['wholesale_discount']
                res[order.id]['wholesale_amount_tax'] = res[order.id]['amount_tax']
                res[order.id]['wholesale_amount_untaxed'] = res[order.id]['wholesale_amount_total'] - res[order.id]['wholesale_amount_tax']
        return res

    # Method override
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _is_price_included_tax(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            price_include_list = []
            res[order.id] = False
            for line in order.order_line:
                if line.taxes_id:
                    for tax in line.taxes_id:
                        price_include_list += [tax.price_include or False]
                else:
                    price_include_list += [False]
            price_include_list = list(set(price_include_list))  # Get unique values of price_include
            if price_include_list:
                if len(price_include_list) > 1:
                    raise osv.except_osv(_('Tax Included in Price Exception!'),
                        _('Mixing between tax included in price and not included in price!'))
                else:
                    res[order.id] = price_include_list[0]
        return res

    _inherit = 'purchase.order'
    _columns = {
        'is_cigarette': fields.boolean('Cigarette'),
        'is_price_included_tax': fields.function(_is_price_included_tax, store=False, string='Tax Included in Price', type='boolean'),
        'wholesale_pricelist_id': fields.many2one('product.pricelist', 'Wholesales Purchase Pricelist', required=False, states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)], 'done': [('readonly', True)]}, help="The wholesale pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities."),
        'wholesale_order_line': fields.one2many('purchase.order.line', 'order_id', 'Order Lines', states={'approved': [('readonly', True)], 'done': [('readonly', True)]}),
        # Whole Sales Amount
        'wholesale_amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'wholesale_amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'wholesale_amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Wholesale Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The total amount"),
        'wholesale_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The total discount"),
        'wholesale_balance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Balance',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The final balance"),
        # Retail Amount
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The amount without tax", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The tax amount"),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'purchase.order.line': (_get_order, None, 10),
            }, multi="sums", help="The total amount"),
    }
    _defaults = {
        'is_cigarette': True,
    }

    def _check_pricelist(self, order):
        if order.wholesale_pricelist_id and order.pricelist_id and \
            order.wholesale_pricelist_id.currency_id.id != order.pricelist_id.currency_id.id:
            raise osv.except_osv(_('Error!'),
                    _('Wholesale Pricelist and Pricelist must be of the same currency!'))

    def create(self, cr, uid, vals, context=None):
        id = super(purchase_order, self).create(cr, uid, vals, context=context)
        order = self.browse(cr, uid, id)
        self._check_pricelist(order)
        return id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(purchase_order, self).write(cr, uid, ids, vals, context=context)
        for order in self.browse(cr, uid, ids):
            self._check_pricelist(order)
        return res

    def onchange_wholesale_pricelist_id(self, cr, uid, ids, pricelist_id, context=None):
        if not pricelist_id:
            return {}
        return {'value': {'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id}}

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        res = super(purchase_order, self).onchange_partner_id(cr, uid, ids, partner_id)
        supplier = self.pool.get('res.partner').browse(cr, uid, partner_id)
        wholesale_pricelist = supplier.property_product_wholesale_pricelist_purchase and supplier.property_product_wholesale_pricelist_purchase.id or False
        val = res.get('value', {})
        if wholesale_pricelist:
            val['wholesale_pricelist_id'] = wholesale_pricelist
        return {'value': val}

    def _update_invoice_flag(self, cr, uid, po_ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        inv_ids = []
        for po in self.browse(cr, uid, po_ids, context=context):
            inv_ids += [invoice.id for invoice in po.invoice_ids]
            invoice_obj.write(cr, uid, inv_ids, {'is_cigarette': po.is_cigarette})
        return True

    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        res = super(purchase_order, self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)
        res.update({'wholesale_price_unit': order_line.wholesale_price_unit or 0.0})
        res.update({'wholesale_unit_discount': order_line.wholesale_unit_discount or 0.0})
        return res

    def action_invoice_create(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).action_invoice_create(cr, uid, ids, context=context)
        self._update_invoice_flag(cr, uid, ids, context=context)
        return res

    def view_invoice(self, cr, uid, ids, context=None):
        res = super(purchase_order, self).view_invoice(cr, uid, ids, context=context)
        self._update_invoice_flag(cr, uid, ids, context=context)
        return res

purchase_order()


class purchase_order_line(osv.osv):

    def _amount_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = {
                'wholesale_price_subtotal': 0.0,
                'price_subtotal': 0.0,
            }
            # Original, for price_subtotal
            price = line.price_unit
            taxes = tax_obj.compute_all(cr, uid, line.taxes_id, price, line.product_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            # Additional, simply multiply qty with price_unit
            wholesale_price = line.wholesale_price_unit - line.wholesale_unit_discount
            wholesale_taxes = tax_obj.compute_all(cr, uid, line.taxes_id, wholesale_price, line.product_qty, line.product_id, line.order_id.partner_id)
            res[line.id]['wholesale_price_subtotal'] = cur_obj.round(cr, uid, cur, wholesale_taxes['total'])
        return res

    _inherit = 'purchase.order.line'
    _columns = {
        'wholesale_price_unit': fields.float('Wholesale Unit Price', required=False, digits_compute=dp.get_precision('Product Price'), multi='line'),
        'wholesale_unit_discount': fields.float('Wholesale Unit Discount', required=False, digits_compute=dp.get_precision('Discount'), multi='line'),
        'wholesale_price_subtotal': fields.function(_amount_line, string='Wholesale Subtotal', digits_compute=dp.get_precision('Account'), multi='line'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account'), multi='line'),
        'wholesale_price_unit_readonly': fields.related('wholesale_price_unit', string='Wholesale Unit Price', readonly=True),
        'price_unit_readonly': fields.related('price_unit', string='Unit Price', readonly=True),
    }

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, context=None):
        res = super(purchase_order_line, self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, context=context)

        product_pricelist = self.pool.get('product.pricelist')
        product_product = self.pool.get('product.product')
        res_partner = self.pool.get('res.partner')

        wholesale_pricelist = context.get('wholesale_pricelist', False)
        if wholesale_pricelist and product_id:
            result = res.get('value', {})
            context_partner = context.copy()
            if partner_id:
                lang = res_partner.browse(cr, uid, partner_id).lang
                context_partner.update({'lang': lang, 'partner_id': partner_id})
            product = product_product.browse(cr, uid, product_id, context=context_partner)
            price = product_pricelist.price_get(cr, uid, [wholesale_pricelist],
                    product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order})[wholesale_pricelist]
            if price == False:
                price = product.wholesale_standard_price
            result.update({'wholesale_price_unit': price})
            res.update({'value': result})

        return res

purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
