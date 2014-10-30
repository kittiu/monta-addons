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


class create_invoices_from_invoice(osv.osv_memory):

    _name = "create.invoices.from.invoice"
    _description = "Create Invoices from Invoice"
    _columns = {
        'num_invoice': fields.integer('Number of Invoice'),
    }
    _defaults = {
        'num_invoice': 1,
    }

    def create_invoices_from_invoice(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        form_data = self.read(cr, uid, ids, ['num_invoice'], context=context)[0]
        context.update({'num_invoice': form_data['num_invoice']})
        return self.pool.get('account.invoice').action_create_invoices_from_invoice(cr, uid, [context['active_id']], context=context)


create_invoices_from_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
