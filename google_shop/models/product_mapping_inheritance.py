# -*- coding: utf-8 -*-
##########################################################################
# MODELO CREADO POR JUAN CAMILO MUÑOZ
# PERMITE LEER LOS DATOS QUE SE IMPORTARON A GOOGLE: ADDITIONAL IMAGES, DESCRIPTION Y LINK
# SE PUEDE VER ESTO EN PRODUCT MAPPING
# LA VISTA QUE RENDERIZA ESTAS FUNCIONES SE LLAMA product_mapping_view_inheritance.xml
##########################################################################

from odoo import models, fields, api


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

    # Traffic metrics fields
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
        """Compute Google traffic metrics for the product.

        This method is a placeholder for integration with Google services.
        Currently it sets default values for clicks, impressions and CTR.
        """
        for rec in self:
            rec.google_clicks = 0
            rec.google_impressions = 0
            rec.google_ctr = 0.0
