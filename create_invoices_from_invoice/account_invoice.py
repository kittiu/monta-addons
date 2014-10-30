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


class account_invoice(osv.osv):

    _inherit = 'account.invoice'
    _columns = {
        'ref_invoice_id': fields.many2one('account.invoice', 'Ref Invoice', readonly=True),
    }

    def action_create_invoices_from_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        num_invoice = context.get('num_invoice', False)
        invoice_ids = []
        invoice_line_obj = self.pool.get('account.invoice.line')
        for x in range(0, num_invoice):
            new_id = self.copy(cr, uid, ids[0], {'ref_invoice_id': ids[0]}, context)
            invoice_ids.append(new_id)
            # Reset quantity
            line_ids = invoice_line_obj.search(cr, uid, [('invoice_id', '=', new_id)])
            invoice_line_obj.write(cr, uid, line_ids, {'quantity': False})
            self.button_reset_taxes(cr, uid, [new_id], context)
        #Show new Invoice
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree2')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, invoice_ids)) + "])]"
        result['name'] = 'Supplier Invoice(s) from an Invoice'
        return result

    def invoice_validate(self, cr, uid, ids, context=None):
        # For invoice with ref_invoice_id, make sure the sum of wholesale_amount_total equal to original
        for invoice in self.browse(cr, uid, ids, context=context):
            if not invoice.ref_invoice_id:
                continue
            # Get the total from old invoice
            old_invoice = invoice.ref_invoice_id
            old_amount_total = old_invoice.wholesale_amount_total
            # Get total of all child invoices
            new_amount_total = 0.0
            child_ids = self.search(cr, uid, [('ref_invoice_id', '=', old_invoice.id), ('state', '!=', 'cancel')])
            for data in self.read(cr, uid, child_ids, ['wholesale_amount_total'], context=context):
                new_amount_total += data['wholesale_amount_total']
            # Check
            if new_amount_total != old_amount_total:
                raise osv.except_osv(_('Error!'), _("""Sum amount of invoices created by %s is not equal to %s itself!
                                                        %s != %s""") % (old_invoice.internal_number, old_invoice.internal_number, new_amount_total, old_amount_total))
        res = super(account_invoice, self).invoice_validate(cr, uid, ids, context=context)
        return res

#     def copy(self, cr, uid, id, default=None, context=None):
#         default = {} if default is None else default.copy()
#         default.update({
#             'ref_invoice_id': False,
#         })
#         return super(account_invoice, self).copy(cr, uid, id, default=default, context=context)

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
