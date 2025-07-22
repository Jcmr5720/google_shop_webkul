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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    admin_email = fields.Char(string="Email")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.default'].sudo().set('res.config.settings',
                                          'admin_email', self.admin_email)
        return res

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['admin_email'] = self.env['ir.default'].sudo().get(
            'res.config.settings', 'admin_email')
        return res
