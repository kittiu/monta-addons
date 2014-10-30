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

{
    'name': 'Customized Jasper Reports',
    'version': '1.0',
    'category': 'Reports',
    'summary': '',
    'description': """
Special for Tax Invoice form. Abilityt to config what to print.
* Address
* PO
* Contact Delivery
* Expected Delivery Date
    """,
    'author': 'kittiu',
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['sale', 'jasper_reports', 'report_menu_restriction'],
    'data': [
        'custom_reports.xml',
        'res_partner_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
