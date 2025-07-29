# -*- coding: utf-8 -*-
from odoo import models, _
import logging
import json
import base64
import requests
import concurrent.futures

_logger = logging.getLogger(__name__)


class ProductGoogleMultiImageBatch(models.Model):
    _inherit = 'product.product'

    def _google_upload_image(self, product_image, google_shop=False, config=False):
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
        data = {
            'data': base64.b64encode(product_image.image_1920).decode('utf-8'),
            'imageType': 'additional',
        }
        try:
            response = requests.post(
                url, headers=headers, data=json.dumps(data), timeout=30
            )
            if response.status_code == 200:
                resp_json = response.json()
                # Google may not return an id; treat 200 as success
                return [resp_json.get("id") or True]
        except Exception as exc:
            _logger.error("Google additional image upload failed %s", exc)
        return []

    def product_google_upload_multi_images(self, google_shop=False, config=False):
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
        image_logs = []
        batch_size = 5
        images_list = list(images)
        for idx in range(0, len(images_list), batch_size):
            batch = images_list[idx:idx + batch_size]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future_to_img = {
                    executor.submit(self._google_upload_image, img, google_shop=google_shop): img
                    for img in batch
                }
                for future in concurrent.futures.as_completed(future_to_img):
                    img = future_to_img[future]
                    try:
                        ids = future.result()
                        if ids:
                            image_ids += ids
                            image_logs.append(_(f"Image {img.id} uploaded successfully"))
                        else:
                            image_logs.append(_(f"Image {img.id} failed to upload"))
                    except Exception as exc:
                        image_logs.append(_(f"Image {img.id} error: {exc}"))

        if image_ids:
            self.write({'google_additional_image_ids': '%s' % (image_ids)})

        mapping = self.env['product.mapping'].search(
            [('product_id', '=', self.id), ('google_shop_id', '=', google_shop.id)],
            limit=1,
        )
        if mapping:
            messages_html = '<ul class="list-unstyled">' + ''.join(
                f'<li>{m}</li>' for m in image_logs
            ) + '</ul>'
            mapping.system_messages = messages_html

        return {'image_ids': image_ids, 'logs': image_logs}
