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
