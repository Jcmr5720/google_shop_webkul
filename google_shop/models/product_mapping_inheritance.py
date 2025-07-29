# -*- coding: utf-8 -*-
##########################################################################
# MODELO CREADO POR JUAN CAMILO MUÑOZ
# PERMITE LEER LOS DATOS QUE SE IMPORTARON A GOOGLE: ADDITIONAL IMAGES, DESCRIPTION Y LINK
# SE PUEDE VER ESTO EN PRODUCT MAPPING
# LA VISTA QUE RENDERIZA ESTAS FUNCIONES SE LLAMA product_mapping_view_inheritance.xml
##########################################################################

from odoo import models, fields, api
import requests
import json
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)


class ProductMappingInheritance(models.Model):
    _inherit = 'product.mapping'

    additional_images = fields.Html(
        string='Additional Images',
        compute='_compute_additional_images',
        readonly=True
    )
    product_shop_link = fields.Char(
        string='Google Product Link',
        compute='_compute_product_shop_link',
        readonly=True
    )
    google_description = fields.Text(
        string='Google Description',
        compute='_compute_google_description',
        readonly=True
    )

    google_clicks = fields.Integer(
        string='Clicks',
        compute='_compute_google_traffic',
        readonly=True
    )
    google_impressions = fields.Integer(
        string='Impressions',
        compute='_compute_google_traffic',
        readonly=True
    )
    google_ctr = fields.Float(
        string='CTR (%)',
        compute='_compute_google_traffic',
        readonly=True
    )
    system_messages = fields.Html(
        string='System Messages',
        compute='_compute_system_messages',
        readonly=True
    )

    @api.depends('product_id')
    def _compute_additional_images(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            html = ''
            if rec.product_id:
                images = self.env['product.image'].search([
                    ('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)
                ])
                for img in images:
                    html += (
                        '<img src="%s/web/image/product.image/%s/image_128" '
                        'style="margin:5px;max-height:128px;"/>'
                    ) % (base_url, img.id)
            rec.additional_images = html

    @api.depends('product_id')
    def _compute_product_shop_link(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            url = ''
            if rec.product_id and rec.product_id.website_url:
                url = base_url.rstrip('/') + rec.product_id.website_url
            rec.product_shop_link = url

    def action_open_product_shop_link(self):
        self.ensure_one()
        if self.product_shop_link:
            return {
                'type': 'ir.actions.act_url',
                'url': self.product_shop_link,
                'target': 'new',
            }
        return False

    @api.depends('product_id')
    def _compute_google_description(self):
        for rec in self:
            desc = ''
            if rec.product_id:
                desc = rec.product_id.website_meta_description or ''
            rec.google_description = desc

    @api.depends('product_id')
    def _compute_google_traffic(self):

        for rec in self:
            clicks = 0
            impressions = 0
            ctr = 0.0

            if rec.google_product_id and rec.google_shop_id and rec.google_shop_id.oauth_id:
                oauth = rec.google_shop_id.oauth_id

                oauth.button_get_token(oauth)

                url = (
                    f"https://shoppingcontent.googleapis.com/content/v2.1/"
                    f"{oauth.merchant_id}/reports/search"
                )
                payload = {
                    "dateRange": {
                        "startDate": (date.today() - timedelta(days=30)).isoformat(),
                        "endDate": date.today().isoformat(),
                    },
                    "dimensions": ["offerId"],
                    "metrics": ["clicks", "impressions", "ctr"],
                    "filters": [
                        {
                            "dimension": "offerId",
                            "operator": "equals",
                            "value": rec.google_product_id,
                        }
                    ],
                }
                headers = {
                    "Authorization": "Bearer " + oauth.access_token,
                    "Content-Type": "application/json",
                }

                try:
                    response = requests.post(
                        url, headers=headers, data=json.dumps(payload), timeout=30
                    )
                    if response.status_code == 200:
                        result = response.json().get("results", [])
                        if result:
                            metrics = result[0].get("metricValues", {})
                            clicks = int(metrics.get("clicks", 0))
                            impressions = int(metrics.get("impressions", 0))
                            ctr = float(metrics.get("ctr", 0.0))
                except Exception as exc:
                    _logger.error("Failed to fetch Google traffic metrics: %s", exc)

            rec.google_clicks = clicks
            rec.google_impressions = impressions
            rec.google_ctr = ctr

    def _compute_system_messages(self):
        for rec in self:
            html = '<ul class="list-unstyled">' + ''.join(
                f'<li>{log.message}</li>' for log in rec.log_ids.sorted('date')
            ) + '</ul>' if rec.log_ids else ''
            rec.system_messages = html
