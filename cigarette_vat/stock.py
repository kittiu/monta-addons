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

from openerp.osv import osv, fields


class stock_picking(osv.osv):

    _inherit = "stock.picking"

    def _prepare_invoice(self, cr, uid, picking, partner, inv_type, journal_id, context=None):
        invoice_vals = super(stock_picking, self)._prepare_invoice(cr, uid, picking, partner, inv_type, journal_id, context=context)
        order = picking.sale_id or picking.purchase_id or False
        invoice_vals['is_cigarette'] = order and order.is_cigarette or False
        return invoice_vals

    def _prepare_invoice_line(self, cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=None):
        invoice_vals = super(stock_picking, self)._prepare_invoice_line(cr, uid, group, picking, move_line, invoice_id, invoice_vals, context=context)
        order = picking.sale_id or picking.purchase_id or False
        if order:
            order_line = move_line.sale_line_id or move_line.purchase_line_id or False
            invoice_vals['wholesale_price_unit'] = order_line and order_line.wholesale_price_unit or 0.0
            invoice_vals['wholesale_unit_discount'] = order_line and order_line.wholesale_unit_discount or 0.0
        return invoice_vals
    
    def _is_cigarette(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            res[picking.id] = False
            if picking.sale_id:
                res[picking.id] = picking.sale_id.is_cigarette or False
            if picking.purchase_id:
                res[picking.id] = picking.purchase_id.is_cigarette or False
        return res
    
    _columns = {
        'is_cigarette': fields.function(_is_cigarette, string='Cigarette', type='boolean'),
    }

stock_picking()


class stock_move(osv.osv):

    _inherit = "stock.move"
    
    # Specifically used for Cigarette, always being standard price (regardless of the selection in product), and Thai Baht
    def _get_reference_accounting_values_for_valuation(self, cr, uid, move, context=None):
        reference_amount, reference_currency_id = super(stock_move, self)._get_reference_accounting_values_for_valuation(cr, uid, move, context=context)
        if move.picking_id.is_cigarette:
            cur_obj = self.pool.get('res.currency')
            cur = move.company_id.currency_id
            product_uom_obj = self.pool.get('product.uom')
            default_uom = move.product_id.uom_id.id
            qty = product_uom_obj._compute_qty(cr, uid, move.product_uom.id, move.product_qty, default_uom)
            # Both in and out
            price_unit = move.product_id.wholesale_standard_price - move.product_id.purchase_vat
            reference_amount = cur_obj.round(cr, uid, cur, qty * price_unit)
        return reference_amount, reference_currency_id

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
