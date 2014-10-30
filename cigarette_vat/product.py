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
import openerp.addons.decimal_precision as dp


class product_product(osv.osv):

    _inherit = 'product.product'
    
    def _get_unit_vat(self, cr, uid, ids, field, arg, context=None):
        res = dict.fromkeys(ids, False)
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                'sale_vat': 0.0,
                'purchase_vat': 0.0,
            }
            for sale_tax in product.taxes_id:
                if sale_tax.price_include:
                    if sale_tax.type == 'fixed':
                        res[product.id]['sale_vat'] += sale_tax.amount
                    elif sale_tax.type == 'percent':
                        res[product.id]['sale_vat'] += product.list_price * ((sale_tax.amount * 100) / (100 + (sale_tax.amount * 100)))
            for purchase_tax in product.supplier_taxes_id:
                if purchase_tax.price_include:
                    if purchase_tax.type == 'fixed':
                        res[product.id]['purchase_vat'] += purchase_tax.amount
                    elif purchase_tax.type == 'percent':
                        res[product.id]['purchase_vat'] += product.standard_price * ((purchase_tax.amount * 100) / (100 + (purchase_tax.amount * 100)))
        return res

    _columns = {
        'wholesale_list_price': fields.float('Wholesale Price', digits_compute=dp.get_precision('Product Price'), help="Base price to compute the customer wholesale price. Sometimes called the catalog price."),
        'wholesale_standard_price': fields.float('Wholesale Cost', digits_compute=dp.get_precision('Product Price'), help="Cost price of the product used for standard stock valuation in accounting and used as a base wholesale price on purchase orders.", groups="base.group_user"),
        'sale_vat': fields.function(_get_unit_vat, string='Vat Included', type='float', digits=(16, 12), help="For included tax of this product, calculate its Vat amount", store=True, multi='vat'),
        'purchase_vat': fields.function(_get_unit_vat, string='Vat Included', type='float', digits=(16, 12), help="For included tax of this product, calculate its Vat amount", store=True, multi='vat'),
    }

product_product()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
