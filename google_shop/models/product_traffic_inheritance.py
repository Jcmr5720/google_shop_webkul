# -*- coding: utf-8 -*-
from odoo import models, fields

class ProductTraffic(models.Model):
    _name = 'product.traffic'
    _description = 'Google Product Traffic'

    product_mapping_id = fields.Many2one('product.mapping', string='Product Mapping', required=True, ondelete='cascade')
    google_shop_id = fields.Many2one(related='product_mapping_id.google_shop_id', string='Shop Name', store=True, readonly=True)
    product_id = fields.Many2one(related='product_mapping_id.product_id', string='Product Name', store=True, readonly=True)
    google_product_id = fields.Char(related='product_mapping_id.google_product_id', string='Google Product Id', store=True, readonly=True)
    country = fields.Many2one(related='product_mapping_id.target_country', string='Country', store=True, readonly=True)
    last_modified_on = fields.Datetime(string='Last Modified On', default=fields.Datetime.now)
    updated = fields.Boolean(related='product_mapping_id.update_status', string='Updated', store=True, readonly=True)
    message = fields.Char(related='product_mapping_id.message', string='Message', store=True, readonly=True)
    clicks = fields.Integer(string='Clicks')
    impressions = fields.Integer(string='Impressions')
