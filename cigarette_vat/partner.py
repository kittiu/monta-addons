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


class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'
    _columns = {
        'property_product_wholesale_pricelist': fields.property(
            'product.pricelist',
            type='many2one',
            relation='product.pricelist',
            domain=[('type', '=', 'sale')],
            string="Wholesale Pricelist",
            view_load=True,
            help="This pricelist will be used, instead of the default one, for sales to the current partner"),
        'property_product_wholesale_pricelist_purchase': fields.property(
          'product.pricelist',
          type='many2one',
          relation='product.pricelist',
          domain=[('type', '=', 'purchase')],
          string="Wholesale Purchase Pricelist",
          view_load=True,
          help="This pricelist will be used, instead of the default one, for purchases from the current partner"),
        'property_account_wholesale_disc_customer': fields.property(
            'product.pricelist',
            type='many2one',
            relation='account.account',
            string="Account Wholesale Discount Customer",
            view_load=True,
            domain="[('type', '=', 'payable')]",
            help="This account will be used instead of the default one as the wholesale discount account for the current partner",
            required=True,
            readonly=True),
        'property_account_wholesale_disc_supplier': fields.property(
            'product.pricelist',
            type='many2one',
            relation='account.account',
            string="Account Wholesale Discount Supplier",
            view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="This account will be used instead of the default one as the wholesale discount account for the current partner",
            required=True,
            readonly=True),
    }

    def _commercial_fields(self, cr, uid, context=None):
        return super(res_partner, self)._commercial_fields(cr, uid, context=context) + ['property_product_wholesale_pricelist']

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
