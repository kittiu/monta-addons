# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Ecosoft Co., Ltd. (http://ecosoft.co.th).
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
    'name': 'Misc Extension to Stock Module',
    'version': '1.0',
    'author': 'Ecosoft',
    'summary': '',
    'description': """

Features:
========

* New field in Delivery Order and Incoming Shipment, "UOM Desc". This will convert in description, 1.5 Lung = 1 Lung and 25 Hor
* Add Car Plate in Delivery Order
* In Product master / Inventory Tab, add new field 'Stock Cost Value' = Quantity on Hand x Wholesale Cost, 'Stock Price Value' = Quantity on Hand x Wholesale Price

""",
    'category': 'Accounting',
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['stock', 'product',
                'picking_invoice_relation',
                'cigarette_vat'],
    'demo': [],
    'data': ['stock_view.xml',
             'product_view.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
