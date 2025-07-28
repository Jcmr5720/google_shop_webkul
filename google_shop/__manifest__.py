# -*- coding: utf-8 -*-
##########################################################################
# Author : Webkul Software Pvt. Ltd. (<https://webkul.com/>;)
# Copyright(c): 2017-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>;
##########################################################################
{
    "name":  "Google Shopping Feed",
    "summary":  """This module allows you to send the products of odoo into google shop.""",
    "category":  "eCommerce",
    "version":  "1.1.10",
    "sequence":  1,
    "author":  "Webkul Software Pvt. Ltd.",
    "license":  "Other proprietary",
    "website":  "https://store.webkul.com/Odoo-Google-Shop.html",
    "description":  """Allows you to send the products of odoo into google shop""",
    "live_test_url":  "https://odoodemo.webkul.com/demo_feedback?module=google_shop",
    "depends":  [
        'base',
        'website_sale',
        'wk_wizard_messages'
    ],
    "data":  [
        'security/google_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/templates.xml',
        'views/google_shop_view.xml',
        'views/oauth2_detail_view.xml',
        'views/google_fields_view.xml',
        'views/field_mapping_view.xml',
        'views/views_product_product.xml',
        'wizard/product_status_views.xml',
        'wizard/debug_wizard_views.xml',
        'views/product_mapping_view.xml',
        'views/product_traffic_view.xml',
        'views/res_config_settings_views.xml',
        'data/cron_data.xml',
    ],
    "demo":  ['demo/demo.xml'],
    "images":  ['static/description/odoo_google_shopping_feed _V15.gif'],
    "application":  True,
    "installable":  True,
    "auto_install":  False,
    "price":  99,
    "currency":  "USD",
}
