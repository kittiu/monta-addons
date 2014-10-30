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
import math


class stock_move(osv.osv):

    _inherit = 'stock.move'

    def _get_uom_desc(self, cr, uid, ids, name, args, context=None):
        res = {}
        for move in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            if move.product_uom and move.product_uom.name == u'ห่อ':
                new_qty = move.product_qty / 50.0
                whole = round(math.floor(new_qty))  # i.e., 2
                frac = round((new_qty - whole) * 50.0)  # i.e., .5
                uom_desc = str(int(whole)) + u' ลัง ' + str(int(frac)) + u' ห่อ'
                res[move.id] = uom_desc
        return res

    _columns = {
        'uom_desc': fields.function(_get_uom_desc, type='char', size=64, string="UoM_Desccription", store=True),
        'picking_id_ref': fields.related('picking_id', 'picking_id_ref', type="many2one", relation="stock.picking", string="Shipping Ref", store=True),
    }

stock_move()


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _get_total_uom_desc(self, cr, uid, ids, name, args, context=None):
        res = {}
        for picking in self.browse(cr, uid, ids, context=context):
            total_product_qty = 0.0
            for move in picking.move_lines:
                if move.product_uom and move.product_uom.name == u'ห่อ':
                    total_product_qty += move.product_qty
            new_qty = total_product_qty / 50.0
            whole = round(math.floor(new_qty))  # i.e., 2
            frac = round((new_qty - whole) * 50.0)  # i.e., .5
            uom_desc = str(int(whole)) + u' ลัง ' + str(int(frac)) + u' ห่อ'
            res[picking.id] = uom_desc
        return res

    _columns = {
        'total_uom_desc': fields.function(_get_total_uom_desc, type='char', size=64, string="UoM_Desccription", store=False),
        'car_plate': fields.char('Car Plate', size=64, required=False),
    }
stock_picking()


class stock_picking_out(osv.osv):

    _inherit = 'stock.picking.out'

    def _get_total_uom_desc(self, cr, uid, ids, name, args, context=None):
        res = self.pool.get('stock.picking')._get_total_uom_desc(cr, uid, ids, name, args, context=context)
        return res

    _columns = {
        'total_uom_desc': fields.function(_get_total_uom_desc, type='char', size=64, string="UoM_Description", store=False),
        'car_plate': fields.char('Car Plate', size=64, required=False),
    }
stock_picking_out()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
