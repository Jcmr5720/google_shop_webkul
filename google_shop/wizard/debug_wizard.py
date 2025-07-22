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

# Python module
import logging
import pprint

_logger = logging.getLogger(__name__)

# Odoo module
from odoo import api, fields, models, _



class ProductStatus(models.TransientModel):
    _name = "google.shop.debug"
    _description = "Debug wizard"

    product_id = fields.Many2one('product.product', 'Product')
    data = fields.Text(string="Data feed", readonly=True)
   
    @api.model
    def genrated_wizard(self):
        res = self.sudo().create({})
        return {
            'name'     : 'Google Shop: Debugger',
            'type'     : 'ir.actions.act_window',
            'res_model': 'google.shop.debug',
            'view_mode': 'form',
            'target'   : 'new',
            'res_id'   : res.id,
            'context'  : {'google_shop':self.env.context.get('google_shop','')},
        }
    
    def dry_run(self):
        try:
            product = self.product_id
            if product:
                google_shop_id = self.env.context.get('google_shop')
                google_shop = self.env['google.shop'].sudo().browse(google_shop_id)
                field_mapping_lines = google_shop.field_mapping_id.field_mapping_line_ids
                base_url = google_shop.shop_url or self.env['ir.config_parameter'].sudo(
                ).get_param('web.base.url')
                data = google_shop.get_mapped_set(product.sudo().read(), field_mapping_lines, base_url, 'insert')
                self.data = pprint.pformat(data[0].get('product',''))
            else:
                raise UserWarning(_("Please select product first."))
        except Exception as e:
            self.data = e
        return {
            'name'     : 'Google Shop: Debugger',
            'type'     : 'ir.actions.act_window',
            'res_model': 'google.shop.debug',
            'view_mode': 'form',
            'target'   : 'new',
            'res_id'   : self.id,
            'context'  : {'google_shop':self.env.context.get('google_shop','')},
        }


