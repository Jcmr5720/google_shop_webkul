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
from odoo import models, fields

OPTIONS = [('string','String'), ('boolean', 'Boolean'), ('number','Number'), ('list', 'List[]'), ('object', 'Object{}'), ('list_object','List+Object[{}]')]
PROPERTYOPTIONS = [('string','String'), ('boolean', 'Boolean'), ('number','Number'), ('list', 'List[]'), ('object', 'Object{}'), ('list_object','List+Object[{}]')]


class Detail_oauth2(models.Model):
    _name = 'google.fields'
    _description = 'Google fields for mapping'
    name = fields.Char(string="Field", required=True)
    required = fields.Boolean(string="Required")
    is_link_field = fields.Boolean(string="Is Url Type", help="You can use this option in case of image and product link type field")
    field_type = fields.Selection(string="Field Type", required=True, help="Data accepted type", selection=OPTIONS, default="string")
    product_property = fields.One2many(
        string='Product property',
        comodel_name='field.property.data',
        inverse_name='google_field_id',
    )


class PropertyData(models.Model):
    _name = 'field.property.data'
    _description = 'Field Property Data'

    name= fields.Many2one(comodel_name="property.data.name", string="Property Name")
    google_field_id = fields.Many2one(string="Google Field", comodel_name="google.fields")
    field_type = fields.Selection(string="Property Field Type", required=True, help="Data accepted type", selection=PROPERTYOPTIONS, default="string")
    # property_object = fields.Many2one(comodel_name="google.fields", string="Property Object Field (If needed)")


class PropertyData(models.Model):
    _name = 'property.data.name'
    _description = 'Property Data Name'

    name= fields.Char(string="Name", required=True)
