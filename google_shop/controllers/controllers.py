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
import werkzeug
from odoo import http
import logging
_logger = logging.getLogger(__name__)


class Google(http.Controller):
    @http.route('/google/<int:record_id>/OAuth2', type="http", auth="public", csrf=False, website=True)
    def oauth2_verify(self, record_id, **kw):
        message = ""
        try:
            if (kw.get("code")):
                oauth2_account_record = http.request.env['oauth2.detail'].sudo().browse(record_id)
                oauth2_account_record.write(
                    {'authorization_code': kw.get("code")})
                message = oauth2_account_record.button_get_code()
                if(message == 'Completed'):
                    return http.request.redirect(oauth2_account_record.account_token_page_url)
                else:
                    return http.request.render('google_shop.error_view_1', {'message': message})
            else:
                return http.request.render('google_shop.error_view_1', {'message': "Somethiong went wrong as the redirect URL entered might be Wrong"})
        except:
            return http.request.render('google_shop.error_view_1', {'message': "Something went Wrong, Please Try Again"})

    @http.route('/verify/website/<string:html_file>', type="http", auth="public", csrf=False, website=True)
    def website_verify(self, html_file, **kw):
        rec = http.request.env["oauth2.detail"].sudo().search(
            [('verify_account_url', '=', html_file)], limit=1)
        if rec:
            return rec.verify_url_data
        else:
            html = http.request.env['ir.ui.view']._render_template(
                'website.page_404', {})
            return werkzeug.wrappers.Response(html, status=404, content_type='text/html;charset=utf-8')
