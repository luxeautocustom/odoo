# -*- coding: utf-8 -*-
# Part of Softhealer Technologies

{
    "name": "Inventory Backdate | Inventory Confirmation Backdate | Backdate In Inventory | Stock Backdate | Warehouse Backdate | Stock Force Date | Inventory Force Date | Inventory Adjustment Force Date",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Warehouse",
    "summary": "Backdate Remarks incoming order backdate delivery order backdate internal transfer backdate receipt Backdate Mass Confirmation Mass Backdate Force Date in Stock Transfer force date stock picking force date receipt force date shipment Odoo",
    "description": """This module is useful for done picking orders (incoming order / delivery order / internal transfer), inventory adjustment and scrap orders with selected backdate. You can put a custom backdate and remarks in the picking & scrap orders. You can mass assign backdate in one click. When you mass assign backdate, it asks for remarks in the mass assign wizard. This selected date and remarks are also reflects in the stock moves & product moves.""",
    "version": "15.0.3",
    "depends": ["stock"],
    "data": [

        'security/ir.model.access.csv',
        'security/backdate_security.xml',
        'wizard/picking_backdate_wizard.xml',
        'wizard/scrap_backdate_wizard.xml',
        'views/stock_config_settings.xml',
        'views/stock_picking.xml',
        'views/stock_move.xml',
        'views/stock_scrap.xml',
        'views/stock_move_line.xml',
        'views/stock_backdate_multi_action.xml',
       
    ],
           
    "auto_install":False,
    "installable": True,
    "application" : True,
    "images": ["static/description/background.png",],     
    "license": "OPL-1",
    "price": 20,
    "currency": "EUR"    
} 
