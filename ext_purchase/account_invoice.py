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


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    def _set_is_boj(self, cr, uid, id, name, value, arg, context=None):
        invoice = self.browse(cr, uid, id, context=context)
        for purchase in invoice.purchase_order_ids:
            self.pool.get('purchase.order').write(cr, uid, [purchase.id], {'is_boj': value}, context=context)
        return True

    def _get_is_boj(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for invoice in self.browse(cursor, user, ids, context=context):
            res[invoice.id] = False
            for purchase in invoice.purchase_order_ids:
                res[invoice.id] = purchase.is_boj
                break
        return res

    _columns = {
        'is_boj': fields.function(_get_is_boj, fnct_inv=_set_is_boj, string='อบจ', type='boolean', store=True),
        'supplier_invoice_number': fields.char('Supplier Invoice Number', size=64, help="The reference of this invoice as provided by the supplier.", readonly=False),

    }
    _defaults = {
        'is_boj': False
    }

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
