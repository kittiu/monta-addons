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


class product_product(osv.osv):

    _inherit = 'product.product'

    def _get_uom_desc(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for product in self.browse(cr, uid, ids, context=context):
            if product.uom_id and product.uom_id.name == u'ห่อ':
                new_qty = product.qty_available / 50.0
                whole = round(math.floor(new_qty))  # i.e., 2
                frac = round((new_qty - whole) * 50.0)  # i.e., .5
                uom_desc = str(int(whole)) + u' ลัง ' + str(int(frac)) + u' ห่อ'
                res[product.id] = uom_desc
        return res

    def _get_wholesale_value(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                'wholesale_cost': 0.0,
                'wholesale_price': 0.0
            }
            res[product.id]['wholesale_cost'] = product.wholesale_standard_price * product.qty_available
            res[product.id]['wholesale_price'] = product.wholesale_list_price * product.qty_available
        return res

    _columns = {
        'uom_desc': fields.function(_get_uom_desc, type='char', size=64, string="UoM_Description", store=False),
        'wholesale_cost': fields.function(_get_wholesale_value, type='float', string="Wholesale Cost", multi="value"),
        'wholesale_price': fields.function(_get_wholesale_value, type='float', string="Wholesale Sales Price", multi="value"),
    }

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
