# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime, timedelta
import requests

from odoo import models, fields

_logger = logging.getLogger(__name__)

class GoogleMerchantShop(models.Model):
    _inherit = 'google.shop'

    def button_fetch_traffic(self):
        for shop in self:
            shop.fetch_product_traffic()
        return self.env['wk.wizard.message'].genrated_message('Traffic data fetched', name='Message')

    def fetch_product_traffic(self):
        """Fetch product traffic information from Google Merchant Center."""
        for shop in self:
            mappings = self.env['product.mapping'].search([('google_shop_id', '=', shop.id)])
            if not mappings:
                continue
            token_result = shop.get_token_status()
            if token_result == 'error':
                continue
            base_url = f"https://shoppingcontent.googleapis.com/content/v2.1/{shop.merchant_id}/reports/search"
            headers = {
                'Authorization': 'Bearer ' + shop.oauth_id.access_token,
                'Content-Type': 'application/json',
            }
            for mapping in mappings:
                payload = {
                    'reportType': 'productPerformance',
                    'dateRange': {
                        'startDate': (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d'),
                        'endDate': datetime.utcnow().strftime('%Y-%m-%d'),
                    },
                    'dimensions': ['offerId', 'country'],
                    'metrics': ['clicks', 'impressions'],
                    'dimensionFilters': [{
                        'dimension': 'offerId',
                        'operator': '==',
                        'expression': mapping.google_product_id,
                    }]
                }
                try:
                    response = requests.post(
                        base_url,
                        headers=headers,
                        data=json.dumps(payload),
                        timeout=30,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for row in data.get('results', []):
                            clicks = int(row.get('metricValues', {}).get('clicks', {}).get('value', 0))
                            impressions = int(row.get('metricValues', {}).get('impressions', {}).get('value', 0))
                            vals = {
                                'product_mapping_id': mapping.id,
                                'clicks': clicks,
                                'impressions': impressions,
                                'last_modified_on': fields.Datetime.now(),
                            }
                            traffic = self.env['product.traffic'].search([('product_mapping_id', '=', mapping.id)], limit=1)
                            if traffic:
                                traffic.write(vals)
                            else:
                                self.env['product.traffic'].create(vals)
                except Exception as exc:
                    _logger.error('Failed to fetch traffic for %s: %s', mapping.google_product_id, exc)
