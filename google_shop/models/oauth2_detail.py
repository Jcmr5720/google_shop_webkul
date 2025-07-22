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

# Python Module

import requests
import json
import logging

# Odoo Module
from odoo.exceptions import UserError
from odoo import models, fields, api, _
from odoo.http import request
from werkzeug import urls

_logger = logging.getLogger(__name__)


class ShopAuth(models.Model):
    """_summary_

    Parameters
    ----------
    models : model

    Raises
    ------
    UserError
        Checking validation
    """
    _name = 'oauth2.detail'
    _inherit = ["mail.thread"]
    _description = 'Account authentications for shop'

    #=== Default Method ===#

    def _default_configuration_calculate(self):
        for record in self:
            email = self.env['res.config.settings'].get_values()[
                'admin_email']
            if not email:
                raise UserError(_("Please insert notification email address in Config settings"))
            record.email = email

    def _default_domain_url_calculate(self):

        IrConfigSudo = self.env['ir.config_parameter'].sudo()
        return IrConfigSudo.get_param('web.base.url', default='')

    # -------------------------------------------------------------------------//
    # MODEL FIELDS
    # -------------------------------------------------------------------------//
    name = fields.Char(string="Token Name", required=True,
                       help="Enter name to your OAuth 2.0")
    email = fields.Char(string="Admin Email",
                        help="Admin Email address", compute="_default_configuration_calculate")
    account_token_page_url = fields.Char(string="Token page url",
                                         help="Token page view url send to user in mail", compute="_compute_token_page_url")
    authorize_url = fields.Char(
        string="Authorize URL", default="https://accounts.google.com/o/oauth2/auth", readonly=True)
    token_url = fields.Char(
        string="Token URL", default="https://accounts.google.com/o/oauth2/token", readonly=True)
    domain_url = fields.Char(string="Shop URL", required=True,
                             help="Domain where You what google to authenticate", default=_default_domain_url_calculate)
    callback_url = fields.Char(string="Callback URL",
                               help="URL where You what google to authenticate", compute="_compute_callback")
    ir_cron_id = fields.Many2one('ir.cron', string='Cron Action',
                                 help='Cron would be use to update product on Google merchant center after a time period...')
    client_id = fields.Char(
        string="Client Id", required=True, help="OAuth 2.0 Client Id")
    client_secret = fields.Char(
        string="Client Secret", required=True, help="OAuth 2.0 Client Secret Id")
    authorization_redirect_url = fields.Char(
        string="Authorization Redirect Url", readonly=True)
    authorization_code = fields.Char(string="Authorization Code")

    # =========================================================================================================================
    config_merchant_detail = fields.Boolean(
        "Configure Merchant Detail", default=False)
    verify_account_url = fields.Char(
        string="URL to Verify", help="URL to verify your Website")
    verify_url_data = fields.Text(
        string="Data in URL", help="Data in your URL")
    merchant_id = fields.Char(string="Merchant ID",
                              help="ID of the Merchant Account")
    # =========================================================================================================================
    access_token = fields.Text(string="Access Token", readonly=True)
    refresh_token = fields.Char(
        string="Refresh Token", readonly=True)
    authentication_state = fields.Selection([('new', 'New'), ('authorize_code', 'Authorize Code'), (
        'error', 'Error'), ('authorize_token', 'Access Token')], default='new')
    _sql_constraints = [('name_unique', 'unique(name)', 'Token Name should be Unique')]

    #=== Romove Token forcefully ===#

    def button_remove_token(self):

        """Method is using by Remove Token button to remove token forcefully
        """
        google_shop_id = self.env['google.shop'].sudo().search([('oauth_id','=',self.id)]).ids
        product_mapping_id = self.env['product.mapping'].sudo().search([('google_shop_id','in',google_shop_id)])
        if product_mapping_id:
            product_mapping_id.unlink()
        self.write({'refresh_token':False,'access_token' :False,'authentication_state' : 'new'})


    #=== Authorize Url ===#

    def button_authorize_url(self):
        """_summary_

        Returns
        -------
        Open authorize url in same tab using odoo action
        """
        self.authorization_redirect_url = self.authorize_url + '?response_type=code&client_id=' + self.client_id + \
            '&redirect_uri=' + self.callback_url + \
            '&scope=https://www.googleapis.com/auth/content' + \
            '&access_type=offline'+'&prompt=consent'
        self.authentication_state = 'authorize_code'
        return {
            'type': 'ir.actions.act_url',
            'url': self.authorization_redirect_url,
            'target': 'self',  # open in a new tab
        }


    #=== Compute Methods ===#

    def _compute_token_page_url(self):
        for page in self:
            page.account_token_page_url = "/web#id="+str(page.id)+"&action="+str(
                page.env.ref("google_shop.oauth2_detail_action").id)+"&model=oauth2.detail&view_type=form"



    # ==========================Button-get-token=======================

    def button_get_token(self, account_id=''):
        if account_id:
            account_tokens = account_id
        else:
            account_tokens = self.env['oauth2.detail'].search([])
        template_id = self.env.ref(
            'google_shop.google_shop_mail_template')
        for token in account_tokens:
            if token.refresh_token:
                data = {'grant_type': 'refresh_token',
                        'refresh_token': token.refresh_token, 'redirect_uri': token.callback_url}

                resp = requests.post(token.token_url, data=data, auth=(
                    token.client_id, token.client_secret), timeout = 30)
                resp = json.loads(resp.text)

                if resp.get('access_token'):
                    try:
                        token.write({
                            "access_token":resp.get('access_token'),
                            "authentication_state":'authorize_token'
                        })
                        if not account_id:
                            connected_accounts = self.env['google.shop'].search(
                                [['shop_status', '!=', 'new']]).filtered(lambda r: r.oauth_id == token)
                            if connected_accounts:
                                for account in connected_accounts:
                                    account.button_update_product(
                                        update_all_product=True)
                        else:
                            return "done"
                    except:
                        token.write({
                            "access_token":None,
                            "authentication_state":'error',
                        })
                        template_id.send_mail(token.id, force_send=True)
                        if account_id:
                            return "error"
                else:
                    token.write({
                            "access_token":None,
                            "refresh_token":None,
                            "authentication_state":'error',
                        })
                    template_id.send_mail(token.id, force_send=True)
                    if account_id:
                        return "error"
            elif not token.refresh_token and account_id:
                return 'error'

    #=== Token Method ===#
    def button_get_code(self):
        """_summary_

        Getting token using code
        """
        message = ""
        data = {'grant_type': 'authorization_code',
                'code': self.authorization_code, 'redirect_uri': self.callback_url}
        resp = requests.post(self.token_url, data=data, verify=True,
                             allow_redirects=True, auth=(self.client_id, self.client_secret), timeout = 30)
        resp = json.loads(resp.text)
        if resp.get('access_token') and resp.get('refresh_token'):
            try:
                self.access_token = resp.get('access_token')
                self.refresh_token = resp.get('refresh_token')
                self.authentication_state = 'authorize_token'
                message = "Completed"
            except:
                self.access_token = None
                self.refresh_token = None
                self.authentication_state = 'error'
                message = str(resp.get('error_description'))
                self.message_post(body=message)
        else:
            odoobot_id = self.env['ir.model.data']._xmlid_to_res_id("base.partner_root")
            self.message_post(body=resp.get('error_description'), author_id=odoobot_id, subject=resp.get('error'))
            self.access_token = None
            self.refresh_token = None
            self.authentication_state = 'error'
            message = "No Data in Authentication Token, Please Check the Entered Detail and Try again"
        return message

    # -------------------------------------------------------------------------
    # ONCHANGE METHODS
    # -------------------------------------------------------------------------

    @api.onchange('domain_url')
    def _compute_callback(self):
        for domain_sequence in self:
            if domain_sequence.domain_url and domain_sequence.id:
                domain_sequence.callback_url = urls.url_join(domain_sequence.domain_url , \
                    f"/google/{str(domain_sequence.id)}/OAuth2")
            else:
                domain_sequence.callback_url = False

