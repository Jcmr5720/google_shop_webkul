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
from odoo.addons.http_routing.models.ir_http import slug
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

FIELDDOMAIN = "[('model','=','product.product'),('ttype','in',('char','boolean','text','float','integer','date','datetime','selection','many2one'))]"
OPTIONS = [('fixed', 'Fixed'), ('dynamic', 'Dynamic')]
MODELOPTIONS = [('attribute', 'Attribute'), ('product', 'Product')]


class FieldMapping(models.Model):
    _name = 'field.mapping.line'
    _rec_name= "google_field_id"
    _description = 'Odoo field mapping with Google fields'
    google_field_id = fields.Many2one(comodel_name='google.fields', string="Google Fields",
                                      help="Select the google field name that you want to map with Odoo field")
    is_link_field = fields.Boolean(related="google_field_id.is_link_field", string="Is link url", help="If google field is a linked type field then we will add data through code for this type of fields")
    field_type = fields.Selection(string="Field Type", related="google_field_id.field_type")
    field_type_value = fields.Selection(string="Field Type Value", default="dynamic", selection=OPTIONS, help="Select type of the data")
    odoo_field_config = fields.Selection(string="Choose odoo model data", default="product", selection=MODELOPTIONS, help="Select type of the odoo field data")
    model_field_id = fields.Many2one(
        comodel_name='ir.model.fields', domain=FIELDDOMAIN)
    field_mapping_id = fields.Many2one(
        comodel_name='field.mapping', help="Field with which you want to map")
    field_mapping_type = fields.Selection(related="field_mapping_id.mapping_type")
    fixed_text = fields.Char(
        string="Fixed Value", help="Fixed data that you want to send")
    default = fields.Char(
        string="Default", help="The data enter here will be send when there is no data in the field")
    is_a_attribute = fields.Boolean(string="Is a attribute", default=False)
    attribute_id = fields.Many2one('product.attribute','Attribute Field')
    property_field_mapping = fields.One2many(
        string='Property field mapping',
        comodel_name='property.field.mapping.line',
        inverse_name='google_property_field_id',
    )


class PropertyFieldMappingline(models.Model):
    _name = 'property.field.mapping.line'
    _description = 'Property Field Mapping Line'
    
    google_property_field_id = fields.Many2one(comodel_name="field.mapping.line")
    google_field_id = fields.Many2one(related="google_property_field_id.google_field_id")
    field_property_data_id = fields.Many2one(comodel_name="field.property.data", domain="[('google_field_id','=', google_field_id)]")
    field_mapping_line_id = fields.Many2one(comodel_name="field.mapping.line", domain="[('field_mapping_type', '=', 'object_field_mapping')]", help="If property accept object type value, then need to create object field mapping already")
    field_type = fields.Selection(string="Property Field Type", related="field_property_data_id.field_type")
    default_value = fields.Char(string="Default Value") 
    odoo_field_id = fields.Many2one(
        comodel_name='ir.model.fields', domain=FIELDDOMAIN, string="Model Field")
    
