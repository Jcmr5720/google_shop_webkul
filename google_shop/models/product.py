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
from odoo import models, fields, api, modules
import logging
#ELIMINAR
import json
import requests

_logger = logging.getLogger(__name__)



class ProductUpdates(models.Model):
    _inherit = 'product.product'
    def all_available_category(self):
        rec = []
        rec_path = modules.get_module_resource('google_shop', 'data', 'categ.txt')
        with open(rec_path) as f:
            for line in f:
                rec.append((line.split('-')[0],line.split('-')[1]))
        return rec
    google_shop_product_categ = fields.Selection(selection=lambda self: self.all_available_category(),string='Google Shop Category')
    #ELIMINAR
    google_additional_image_ids = fields.Char(string='Google Additional Image IDs')

    def write(self, vals):
        res = super(ProductUpdates, self).write(vals)
        fields_dict = self.env['field.mapping.line'].sudo().search(
            [('field_type_value', '=', 'dynamic')])
        fields_name = [x['model_field_id']['name'] for x in fields_dict]
        fields_name.append('name')
        common_list = list(set.intersection(set(fields_name), set(vals)))
        if len(common_list) > 0:
            for s in self:
                self.env['product.mapping'].sudo().search([('product_id', '=', s.id)]).write(
                    {'product_status': 'updated', 'update_status': False})
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for rec in self:
            variant_ids = rec.product_variant_ids
            if 'is_published' in vals:
                active_variants = variant_ids.filtered(lambda r: r.active)
                product_mapping_id = self.env['product.mapping'].sudo().search(
                    [('product_id', 'in', active_variants.ids)])
                if product_mapping_id:
                    product_mapping_id.write(
                        {'product_status': 'updated', 'update_status': False})
        return res

        
#---NUEVA EDICION----


class ProductGoogleMultiImage(models.Model):
    _inherit = 'product.product'

    def _google_upload_image(self, product_image, google_shop=False, config=False):
        """Upload a single image to Google Merchant and return the image id.

        The previous implementation uploaded raw image bytes which could be
        considerably slower especially for large images.  Google also accepts a
        publicly accessible URL for the image so here we send the image link
        instead of the binary payload.
        """
        google_shop = google_shop or config
        if not google_shop:
            return []
        if not product_image.image_1920:
            return []

        google_shop.oauth_id.button_get_token(google_shop.oauth_id)
        url = (
            f"https://shoppingcontent.googleapis.com/content/v2.1/"
            f"{google_shop.merchant_id}/products/{self.default_code}/images:insert"
        )
        headers = {
            'Authorization': 'Bearer ' + google_shop.oauth_id.access_token,
            'Content-Type': 'application/json',
        }

        base_url = google_shop.shop_url or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        link = f"{base_url}/web/image/product.image/{product_image.id}/image_1024"
        data = {
            'image': {'link': link},
            'imageType': 'additional',
        }

        try:
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=30)
            if response.status_code == 200:
                resp_json = response.json()
                return [resp_json.get('id')] if resp_json.get('id') else []
        except Exception as exc:
            _logger.error('Google additional image upload failed %s', exc)
        return []

    def product_google_upload_multi_images(self, google_shop=False, config=False):
        """Upload all available images of this product to Google Merchant."""
        google_shop = google_shop or config
        if not google_shop:
            return {'error': 'google shop configuration missing', 'status': 'error'}

        images = self.env['product.image'].search([('product_tmpl_id', '=', self.product_tmpl_id.id)])
        if not images:
            return {
                'error': 'product_google_upload_multi_images error no images to upload',
                'status': 'error',
                'message': 'no images to upload',
            }

        image_ids = []
        for product_image in images:
            image_ids += self._google_upload_image(product_image, google_shop=google_shop)
            self.write({'google_additional_image_ids': '%s' % (image_ids)})
        return image_ids