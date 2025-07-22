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

#Python Modules
import logging
import requests
import json
from datetime import datetime


#Odoo Modules
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductMapping(models.Model):
    _name = 'product.mapping'
    _description = 'Product mapping result after export or update products'

    # -------------------------------------------------------------------------//
    # MODEL FIELDS
    # -------------------------------------------------------------------------//

    google_shop_id = fields.Many2one(
        comodel_name='google.shop', string="Shop Name", required=True)
    product_id = fields.Many2one(
        comodel_name='product.product', string="Product Name", required=True, ondelete='cascade')
    update_status = fields.Boolean(string="Updated", default=True)
    product_status = fields.Selection(
        [('updated', 'Done'), ('error', 'Error')])
    google_product_id = fields.Char(string="Google Product Id")
    message = fields.Char(string="Message")
    product_expire_date_on_mc = fields.Datetime(string="Expire Date on MC")
    destination_status = fields.Char(string="Destination Status")
    approvedCountries = fields.Char(string="Approved Countries")
    pendingCountries = fields.Char(string="Pending Countries")
    disapproved_countries = fields.Char(string="Disapproved Countries")
    wk_fetched_issues = fields.Html(string="Fetched Issues")
    image_128 = fields.Image(related='product_id.image_128')
    content_language = fields.Many2one(string="Content Language", comodel_name="res.lang",
                                       required=True)
    target_country = fields.Many2one(string="Country", comodel_name="res.country",
                                     required=True)


    #=== CRUD METHODS ===#

    def unlink(self):
        oauth2_error, error_count, done_count = 0, 0, 0
        chunk_products= [self[n:n+500] for n in range(0,len(self),500)]
        token_accounts = self.env['oauth2.detail'].search([('merchant_id','!=',False)])
        for product in chunk_products:
            update_state_products,error_state_products = product.filtered(lambda r:r.product_status == 'updated'),product.filtered(lambda r:r.product_status != 'updated')
            for account in token_accounts:
                account.button_get_token(account)
                merchant_products = update_state_products.filtered(lambda r: r.google_shop_id.merchant_id == account.merchant_id)
                entries = [{"batchId":val.id,"merchantId":val.google_shop_id.merchant_id,"method":"delete","productId":val.google_product_id} for val in merchant_products]
                try:
                    api_call_headers = {'Authorization': "Bearer " +account.access_token, 'Content-Type': 'application/json'}
                    api_call_response = requests.post('https://shoppingcontent.googleapis.com/content/v2.1/products/batch',
                                              headers=api_call_headers, data=json.dumps({"entries":entries}), verify=True)
                    if api_call_response.status_code == 200:
                        res=super(ProductMapping,merchant_products).unlink()
                        done_count+= len(merchant_products)
                    elif api_call_response.status_code == 401:
                        oauth2_error+=1
                except Exception as e:
                    error_count+=len(merchant_products)
                if error_state_products:
                    res=super(ProductMapping,error_state_products).unlink()
                    done_count+= len(error_state_products)
        return (oauth2_error, error_count, done_count)

    def _get_product_details_for_merchant_api(self):
        product_details = []
        for rec in self:
            batchId = rec.id
            merchantId = rec.google_shop_id.merchant_id
            method = "get"
            productId = rec.google_product_id
            product_details.append({'batchId':batchId,'merchantId':merchantId,'method':method,'productId':productId})
        return {'entries': product_details}

    # -------------------------------------------------------------------------
    # SERVER ACTION
    # -------------------------------------------------------------------------
    def product_get_status_server_action(self):
        #Generating access token

        # if self._context.get('active_ids'):
            shop_ids = self.env['google.shop'].search([])
            for shop in shop_ids:
                token_result = shop.get_token_status()
                if token_result == 'error':
                    return shop.env['wk.wizard.message'].genrated_message("Please check authorize your account...", name='Message')

                else:
                    list_selected_mapping = len(self)
                    while list_selected_mapping > 0:
                        product_to_get_status = self[:500]
                        products = product_to_get_status._get_product_details_for_merchant_api()
                        api_call_headers = {'Authorization': "Bearer " +
                                            shop.oauth_id.access_token, 'Content-Type': 'application/json'}
                        api_call_response = requests.post('https://shoppingcontent.googleapis.com/content/v2.1/productstatuses/batch',
                                                        headers=api_call_headers, data=json.dumps(products), verify=True)
                        if api_call_response.status_code == 200:
                            response_data = api_call_response.json()
                            response_entries = response_data.get('entries')
                            if response_entries[0].get('errors'):
                                product_to_get_status.write({'wk_fetched_issues':response_entries[0].get('errors')['errors']})
                            else:
                                for response in response_data.get('entries'):
                                    mapped_product = self.browse(response.get('batchId',''))
                                    # mapped_product = product_to_get_status.filtered(lambda a: a.google_shop_id == shop and a.google_product_id == response.get('productStatus').get('productId'))
                                    if mapped_product and not response.get('errors',''):
                                        product_expire_date_on_mc = datetime.fromisoformat(response.get('productStatus').get('googleExpirationDate').replace("Z", "+00:00")).replace(tzinfo=None)
                                        approvedCountries = response.get('productStatus')['destinationStatuses'][0].get('approvedCountries','')
                                        pendingCountries = response.get('productStatus')['destinationStatuses'][0].get('pendingCountries','')
                                        disapprovedCountries = response.get('productStatus')['destinationStatuses'][0].get('disapprovedCountries','')
                                        destination_status = response.get('productStatus')['destinationStatuses'][0].get('status','')
                                        wk_fetched_issues = response.get('productStatus').get('itemLevelIssues', False)
                                        mapped_product.write({
                                            'product_expire_date_on_mc':product_expire_date_on_mc,
                                            'destination_status':destination_status,
                                            'pendingCountries': pendingCountries,
                                            'approvedCountries':approvedCountries,
                                            'disapproved_countries':disapprovedCountries,
                                            'wk_fetched_issues':wk_fetched_issues if wk_fetched_issues else '',
                                        })
                                    else:
                                        mapped_product.write({'wk_fetched_issues':response.get('errors')['errors']})
                        self = self[500:]
                        list_selected_mapping = len(self)

    def product_map_status_server_action(self):
        wizard_id = self.env['product.status'].create(
            {'selective_product_mapping_ids': [(6, 0, self._context['active_ids'])]})
        return {
            "name": "Mark selective products update status as:",
            "type": "ir.actions.act_window",
            "res_model": "product.status",
            'res_id': wizard_id.id,
            "view_id": self.env.ref("google_shop.product_status_form").id,
            "view_mode": "form",
            "target": "new",
        }

    # -------------------------------------------------------------------------
    # DEPENDS METHODS
    # -------------------------------------------------------------------------
    @api.depends('google_shop_id', 'product_id')
    def name_get(self):
        result = []
        for mapping in self:
            name = "[" + mapping.google_shop_id.name + "]" + \
                ' ' + mapping.product_id.name
            result.append((mapping.id, name))
        return result
