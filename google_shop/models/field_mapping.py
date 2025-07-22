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

OPTIONS= [('google_field_mapping', 'Used for google field mapping'), ('object_field_mapping', 'Used for object field mapping')]

class FieldMapping(models.Model):
    _name = 'field.mapping'
    _description = 'Fields for mapping'
    name = fields.Char(string="Name", required=True)
    active = fields.Boolean(string="Active", default=True)
    mapping_type = fields.Selection(selection=OPTIONS, string="Mapping Type", default="google_field_mapping")
    field_mapping_line_ids = fields.One2many(
        comodel_name='field.mapping.line', inverse_name='field_mapping_id', string="Fields To Mapped")
    



