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
from odoo import models, fields, modules
import logging
from odoo.tools import misc
_logger = logging.getLogger(__name__)

class ProductUpdates(models.Model):
    _name = 'target.country'
   
    
    shop_id=fields.Many2one('google.shop',string='Shop Id')
    target_country = fields.Many2one(string="Country", comodel_name="res.country", 
                                     domain=lambda self: [('code', 'in', self.country_list),('id','!=',self.shop_id.target_country.id)])

    country_list = [ 'FR', 'IN', 'DZ', 'AO', 'AR', 'AU', 'AT', 'BH', 'BD', 'BY', 'BE', 'BR', 'KH', 'CM', 'CA', 'CL', 'CO', 'CR', 'CI', 'CZ', 'DK', 'DO', 'EC', 'EG', 'SV', 'ET', 'FI', 'GE', 'DE', 'GH', 'GR', 'GT', 'HK', 'HU', 'ID', 'IE', 'IL', 'IT', 'JP', 'JO', 'KZ', 'KE', 'KW', 'LB', 'MG', 'MY', 'MU', 'MX', 'MA', 'MZ', 'MM', 'NP', 'NL', 'NZ', 'NI', 'NG', 'NO', 'OM', 'PK', 'PA', 'PY', 'PE', 'PH', 'PL', 'PT', 'PR', 'RO', 'RU', 'SA', 'SN', 'SG', 'SK', 'ZA', 'KR', 'ES', 'LK', 'SE', 'CH', 'TW', 'TZ', 'TH', 'TN', 'TR', 'UG', 'UA', 'AE', 'GB', 'US', 'UY', 'UZ', 'VE', 'VN', 'ZM', 'ZW' ]
    content_language = fields.Many2one(string="Content Language", comodel_name="res.lang",
                                       required=True, help="Language in which your products will get sync on Google Shop")