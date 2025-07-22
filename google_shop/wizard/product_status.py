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
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProductStatus(models.TransientModel):
    _name = "product.status"
    _description = "Change product status in Product Mapping"
    selective_product_mapping_ids = fields.Many2many(
        'product.mapping', 'product_mapping_wizard_data', 'product_status_wizard_data', 'selective_product_mapping_data')
    manage_product_status = fields.Selection(
        [('updated', 'Updated'), ('not_updated', 'Not updated')], default='updated', string="Product Status")

    def apply_on_all_selective_product(self):
        if self.selective_product_mapping_ids:
            if self.manage_product_status == 'updated':
                status = True
            else:
                status = False
            for product in self.selective_product_mapping_ids:
                product.write({'update_status': status})
