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


class purchase_order(osv.osv):

    _inherit = 'purchase.order'
    _columns = {
        'is_boj': fields.boolean('อบจ', states={'confirmed': [('readonly', True)], 'approved': [('readonly', True)], 'done': [('readonly', True)]}),
        'partner_ref': fields.char('Supplier Reference', size=64,
            help="Reference of the sales order or quotation sent by your supplier. It's mainly used to do the matching when you receive the products as this reference is usually written on the delivery order sent by your supplier."),

    }
    _defaults = {
        'is_boj': False
    }
purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
