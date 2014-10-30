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


class sale_shop(osv.osv):
    _inherit = "sale.shop"
    _columns = {
        'wholesale_pricelist_id': fields.many2one('product.pricelist', 'Wholesale Pricelist'),
    }

sale_shop()


class sale_order(osv.osv):

    # Method override
    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                # Wholesale
                'wholesale_amount_untaxed': 0.0,
                'wholesale_amount_tax': 0.0,
                'wholesale_amount_total': 0.0,
                'wholesale_discount': 0.0,
                'wholesale_balance': 0.0,
                # Retail
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
            }
            # Original as Retail
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
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
                    val_discount += line.wholesale_unit_discount * line.product_uom_qty
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
                    val_total += wholesale_price * line.product_uom_qty
                    val_discount += line.wholesale_unit_discount * line.product_uom_qty
                res[order.id]['wholesale_balance'] = cur_obj.round(cr, uid, cur, val_total)
                res[order.id]['wholesale_discount'] = cur_obj.round(cr, uid, cur, val_discount)
                res[order.id]['wholesale_amount_total'] = res[order.id]['wholesale_balance'] + res[order.id]['wholesale_discount']
                res[order.id]['wholesale_amount_tax'] = res[order.id]['amount_tax']
                res[order.id]['wholesale_amount_untaxed'] = res[order.id]['wholesale_amount_total'] - res[order.id]['wholesale_amount_tax']

        return res

    # Method override
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    def _is_price_included_tax(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            price_include_list = []
            res[order.id] = False
            for line in order.order_line:
                if line.tax_id:
                    for tax in line.tax_id:
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

    _inherit = 'sale.order'
    _columns = {
        'is_cigarette': fields.boolean('Cigarette'),
        'is_price_included_tax': fields.function(_is_price_included_tax, store=False, string='Tax Included in Price', type='boolean'),
        'wholesale_pricelist_id': fields.many2one('product.pricelist', 'Wholesales Pricelist', required=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Wholesale Pricelist for current sales order."),
        'wholesale_order_line': fields.one2many('sale.order.line', 'order_id', 'Order Lines', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}),
        # Whole Sales Amount
        'wholesale_amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'wholesale_amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'wholesale_amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Wholesale Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),
        'wholesale_discount': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Discount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total discount."),
        'wholesale_balance': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Balance',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The final balance."),
        # Retail Amount
        'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Untaxed Amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The amount without tax.", track_visibility='always'),
        'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Taxes',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The tax amount."),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Retail Total',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['wholesale_order_line', 'order_line'], 10),
                'sale.order.line': (_get_order, ['wholesale_price_unit', 'wholesale_unit_discount', 'price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums', help="The total amount."),

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
        new_id = super(sale_order, self).create(cr, uid, vals, context=context)
        order = self.browse(cr, uid, new_id)
        self._check_pricelist(order)
        return new_id

    def write(self, cr, uid, ids, vals, context=None):
        res = super(sale_order, self).write(cr, uid, ids, vals, context=context)
        for order in self.browse(cr, uid, ids):
            self._check_pricelist(order)
        return res

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals.update({'is_cigarette': order.is_cigarette})
        return invoice_vals

    def onchange_wholesale_pricelist_id(self, cr, uid, ids, pricelist_id, order_lines, context=None):
        context = context or {}
        if not pricelist_id:
            return {}
        value = {
            'currency_id': self.pool.get('product.pricelist').browse(cr, uid, pricelist_id, context=context).currency_id.id
        }
        if not order_lines:
            return {'value': value}
        warning = {
            'title': _('Pricelist Warning!'),
            'message': _('If you change the pricelist of this order (and eventually the currency), prices of existing order lines will not be updated.')
        }
        return {'warning': warning, 'value': value}

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context=context)
        part = self.pool.get('res.partner').browse(cr, uid, part, context=context)
        wholesale_pricelist = part.property_product_wholesale_pricelist and part.property_product_wholesale_pricelist.id or False
        val = res.get('value', {})
        if wholesale_pricelist:
            val['wholesale_pricelist_id'] = wholesale_pricelist
        return {'value': val}

    def onchange_shop_id(self, cr, uid, ids, shop_id, context=None):
        res = super(sale_order, self).onchange_shop_id(cr, uid, ids, shop_id, context=context)
        v = res.get('value', {})
        if shop_id:
            shop = self.pool.get('sale.shop').browse(cr, uid, shop_id, context=context)
            if shop.wholesale_pricelist_id.id:
                v['wholesale_pricelist_id'] = shop.wholesale_pricelist_id.id
        return {'value': v}

sale_order()


class sale_order_line(osv.osv):

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
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            cur = line.order_id.pricelist_id.currency_id
            res[line.id]['price_subtotal'] = cur_obj.round(cr, uid, cur, taxes['total'])
            # Additional, simply multiply qty with price_unit
            wholesale_price = line.wholesale_price_unit - line.wholesale_unit_discount
            wholesale_taxes = tax_obj.compute_all(cr, uid, line.tax_id, wholesale_price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            res[line.id]['wholesale_price_subtotal'] = cur_obj.round(cr, uid, cur, wholesale_taxes['total'])
        return res

    _inherit = 'sale.order.line'
    _columns = {
        'wholesale_price_unit': fields.float('Wholesale Unit Price', required=False, digits_compute=dp.get_precision('Product Price'), readonly=True, states={'draft': [('readonly', False)]}),
        'wholesale_unit_discount': fields.float('Wholesale Unit Discount', required=False, digits_compute=dp.get_precision('Discount'), readonly=True, states={'draft': [('readonly', False)]}),
        'wholesale_price_subtotal': fields.function(_amount_line, string='Wholesale Subtotal', digits_compute=dp.get_precision('Account'), multi='line'),
        'price_subtotal': fields.function(_amount_line, string='Subtotal', digits_compute=dp.get_precision('Account'), multi='line'),
        'wholesale_price_unit_readonly': fields.related('wholesale_price_unit', string='Wholesale Unit Price', readonly=True),
        'price_unit_readonly': fields.related('price_unit', string='Unit Price', readonly=True),
    }

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
                    uom, qty_uos, uos, name, partner_id,
                    lang, update_tax, date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        wholesale_pricelist = context.get('wholesale_pricelist', False)
        if wholesale_pricelist and product:
            result = res.get('value', {})
            domain = res.get('domain', {})
            warning = res.get('warning', {})
            warning_msgs = ''

            price = self.pool.get('product.pricelist').price_get(cr, uid, [wholesale_pricelist],
                    product, qty or 1.0, partner_id, {
                        'uom': uom or result.get('product_uom'),
                        'date': date_order,
                        })[wholesale_pricelist]
            if price is False:
                warn_msg = _("Cannot find a wholesale pricelist line matching this product and quantity.\n"
                        "You have to change either the product, the quantity or the wholesale pricelist.")

                warning_msgs += _("No valid wholesale pricelist line found ! :") + warn_msg + "\n\n"
            else:
                result.update({'wholesale_price_unit': price})

            if warning_msgs:
                warning = {
                           'title': _('Configuration Error!'),
                           'message': warning_msgs
                        }
            return {'value': result, 'domain': domain, 'warning': warning}
        else:
            return res

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=False, context=context)
        if not line.invoiced:
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            wholesale_pu = 0.0
            if uosqty:
                wholesale_pu = round(line.wholesale_price_unit * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
                wholesale_ud = round(line.wholesale_unit_discount * line.product_uom_qty / uosqty,
                        self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))
                res.update({'wholesale_price_unit': wholesale_pu})
                res.update({'wholesale_unit_discount': wholesale_ud})
        return res

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
