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
import pytz
import requests
import json
import logging
from datetime import datetime, timedelta
from ast import literal_eval
from markupsafe import Markup

# Odoo Module
from odoo.exceptions import UserError, ValidationError
from odoo.addons.http_routing.models.ir_http import slug
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)
UTC = pytz.utc


JUNKMAPPING = []
GOOLEREQUIREDFIELDS = []
REQUIREDFIELDVALIDATION = ''
REQUIREDFIELDVALIDATION = False

BATCHAPI = "https://shoppingcontent.googleapis.com/content/v2.1/products/batch"
AUTHAPI = "https://www.googleapis.com/content/v2.1/"


class GoogleMerchantShop(models.Model):
    _name = 'google.shop'
    _inherit = ["mail.thread"]
    _description = 'Shop for performing operation on products for merchant center'
    name = fields.Char(string="Name", required=True)

    # === Default Method ===#

    def _default_website(self):
        return self.env['website'].get_current_website()

    def _default_pricelist(self):
        return self.env['website'].get_current_website().get_current_pricelist()

    # -------------------------------------------------------------------------//
    # MODEL FIELDS
    # -------------------------------------------------------------------------//
    domain_input = fields.Char(string="Domain", default="[]")
    limit = fields.Integer(string="Limit", default=10)

    channel = fields.Selection([("online", "Online"), ("local", "Local")], string="Channel",
                               required=True, help="Select that whether your store is Online or Offline")
    product_selection_type = fields.Selection([('domain', 'Domain'), ('manual', 'Manual')], default="domain",
                                              string="Product Select Way", help="Select whether you want to select the product manually or with the help of domain")
    merchant_id = fields.Char(name="Merchant Id", help="Merchant Id of your merchant account",
                              related="oauth_id.merchant_id", readonly=True)
    shop_status = fields.Selection(
        [('new', 'New'), ('validate', 'Validate'), ('error', 'Error'), ('done', 'Done')], default='new')
    currency_id = fields.Many2one(
        string="Currency", store=True, related="product_pricelist_id.currency_id")
    website_id = fields.Many2one(
        'website', string="website", default=_default_website)

    oauth_id = fields.Many2one(string="Account", comodel_name="oauth2.detail", required=True,
                               help="Select the account with which you want to sync the products")
    content_language = fields.Many2one(string="Content Language", comodel_name="res.lang",
                                       required=True, help="Language in which your products will get sync on Google Shop")
    target_country = fields.Many2one(string="Target Country", comodel_name="res.country",domain=lambda self: [('code', 'in', self.country_list)],
                                     required=True, help="Select the country in which you want to sell the products")
    
    country_list = [ 'FR', 'IN', 'DZ', 'AO', 'AR', 'AU', 'AT', 'BH', 'BD', 'BY', 'BE', 'BR', 'KH', 'CM', 'CA', 'CL', 'CO', 'CR', 'CI', 'CZ', 'DK', 'DO', 'EC', 'EG', 'SV', 'ET', 'FI', 'GE', 'DE', 'GH', 'GR', 'GT', 'HK', 'HU', 'ID', 'IE', 'IL', 'IT', 'JP', 'JO', 'KZ', 'KE', 'KW', 'LB', 'MG', 'MY', 'MU', 'MX', 'MA', 'MZ', 'MM', 'NP', 'NL', 'NZ', 'NI', 'NG', 'NO', 'OM', 'PK', 'PA', 'PY', 'PE', 'PH', 'PL', 'PT', 'PR', 'RO', 'RU', 'SA', 'SN', 'SG', 'SK', 'ZA', 'KR', 'ES', 'LK', 'SE', 'CH', 'TW', 'TZ', 'TH', 'TN', 'TR', 'UG', 'UA', 'AE', 'GB', 'US', 'UY', 'UZ', 'VE', 'VN', 'ZM', 'ZW' ]
    target_country_ids = fields.One2many(string="Target Countrys", comodel_name="target.country",inverse_name='shop_id',
                                     required=True, help="Select the country in which you want to sell the products")
    product_pricelist_id = fields.Many2one(comodel_name="product.pricelist", string="Product Pricelist", required=True,
                                           help="select the pricelist according to which your product price will get selected", default=_default_pricelist)
    field_mapping_id = fields.Many2one(comodel_name="field.mapping", string="Field Mapping", domain=[
                                       ('active', '=', True)], required=True)
    product_ids_rel = fields.Many2many(comodel_name='product.product', relation='merchant_shop_product_rel', column1='google_id', column2='product_id', domain=[
                                       ("sale_ok", "=", True), ("website_published", "=", True)], string="Products")
    shop_url = fields.Char(name="Shop URL", help="Write your domain name of your website",
                           related="oauth_id.domain_url", readonly=True)
    mapping_count = fields.Integer(
        string="Total Mappings", compute="_mapping_count")
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Name should be Unique')]

    @api.onchange('field_mapping_id')
    def _onchange_field_mapping(self):
        field_mapping_ids = self.env['field.mapping'].search([])
        if field_mapping_ids:
            self.field_mapping_id = min(field_mapping_ids.ids)

    def _get_product_domain(self):
        f_domain = [("sale_ok", "=", True), ("website_published", "=",
                                             True), ('website_id', 'in', (self.website_id.id, False))]
        return f_domain
    
    def reset_state(self):
        for rec in self:
            rec.shop_status = 'new'

    def error_log(self, message, content):
        _logger.info(" <<  {}  >>{}".format(message, content))
        
    @api.constrains('target_country_ids')
    def check_country(self):
          if len(self.target_country_ids) != len(self.target_country_ids.mapped("target_country")):
                raise ValidationError("countries must be unique .")

    def manage_error_products(self):
        error_state_records = self.env['product.mapping'].search(
            [('product_status', '=', 'error'), ('google_shop_id', '=', self.id)])
        done_state_records_product = self.env['product.mapping'].search(
            [('product_status', '=', 'updated'), ('google_shop_id', '=', self.id)]).mapped('product_id').ids
        if error_state_records:
            for record in error_state_records:
                if record.product_id.id in done_state_records_product:
                    record.unlink()

    def product_ids_domain_or_manual(self, mapped_products_product_ids, error_products_product_ids):
        if (self.product_selection_type == 'domain'):
            try:
                fixed_domain = self._get_product_domain(
                ) + [('id', 'not in', mapped_products_product_ids)]
                limit = self.limit-len(error_products_product_ids) if (
                    self.limit-len(error_products_product_ids)) > 0 else 0
                if self.domain_input:
                    final_domain = literal_eval(
                        self.domain_input) + fixed_domain
                else:
                    final_domain = fixed_domain
                if limit == 0:
                    product_ids = []
                else:
                    product_ids = self.env["product.product"].search(
                        final_domain, limit=limit).ids
            except:
                return self.env['wk.wizard.message'].genrated_message("Enter Domain Properly", name='Message')
        else:
            product_ids = self.product_ids_rel.ids
        return product_ids

    def _manage_product_for_api(self, all_products_to_be_upload, context, updation_type):
        total_product = 0
        done_count = 0
        error_msg = ''
        batch_of_all_products = {}
        total_no_of_products = len(all_products_to_be_upload)
        while total_no_of_products > 0:
            if total_no_of_products > 1000:
                product_to_update = all_products_to_be_upload[:1000]
                batch_of_all_products["entries"] = product_to_update
                all_products_to_be_upload = all_products_to_be_upload[1000:]
                total_no_of_products = len(
                    all_products_to_be_upload)
            else:
                batch_of_all_products["entries"] = all_products_to_be_upload
                total_no_of_products = 0
            response = self.with_context(
                context).call_google_insert_api(batch_of_all_products)
            if response.status_code != 200:
                response_content = literal_eval(response.text)
                message = response_content.get("error")
                self.error_log("Export Response Error", message)
                return self.env['wk.wizard.message'].genrated_message(message, name='Message')

            if updation_type == "update":
                total_product, done_count, error_msg = self.manage_update_response_of_api(
                    response, total_product, done_count)
                if error_msg:
                    return error_msg
            else:
                total_product, done_count, error_msg = self.manage_insert_response_of_api(
                    response, total_product, done_count)
                if error_msg:
                    return error_msg
        if updation_type == "update":
            message = ("{0} out of {1} products are updated".format(
                done_count, total_product))
        else:
            message = ("{0} out of {1} products are exported".format(
                done_count, total_product))
            self.manage_error_products()
            if done_count == total_product:
                self.shop_status = "done"
        return self.env['wk.wizard.message'].genrated_message(message, name='Message')

    def manage_insert_response_of_api(self, response, total_product, done_count):

        call_response = response.json()
        error_msg = ''
        if response.status_code == 401:
            self.shop_status = "error"
            message = "Account ID might had been expired so, refresh it and try again"
            raise UserError(_(message))
        elif response.status_code == 200:
            if 'entries' in call_response.keys():
                all_products_response = call_response['entries']
                for response in all_products_response:
                    total_product += 1
                    if 'kind' and 'batchID' and 'product' in response.keys():
                        update_status = True
                        product_status = 'updated'
                        msg = "Product is exported Successfully"
                        google_product_ids = response['product']['id']
                    else:
                        update_status = False
                        product_status = 'error'
                        msg = response['errors']['message']
                        google_product_ids = None
                    product_id=self.env['product.product'].search([('default_code','=',response.get("product").get("offerId"))])
                    if response['batchId'] in JUNKMAPPING:
                      
                        self.env['product.mapping'].search([('product_id','=',product_id)], limit=1).write({
                            'update_status': update_status,
                            'product_status': product_status,
                            'message': msg,
                            'google_product_id': google_product_ids})
                    else:
                        # country=self.env['res.country'].search([('code','=',response.get('targetCountry'))])
                        if response.get("product"):
                            target_country=self.env['res.country'].search([('code','=',response.get("product").get("targetCountry"))]).id
                            
                            country = self.target_country_ids.filtered(lambda line: line.target_country.id == target_country)
                            if self.target_country.id==target_country:
                                content_language=self.content_language.id
                            else:
                                content_language=country.content_language.id
                           
                           
                            self.env['product.mapping'].create({
                                'google_shop_id': self.id,
                                'product_id': product_id.id,
                                'update_status': update_status,
                                'product_status': product_status,
                                'message': msg,
                                'target_country':target_country,
                                'content_language':content_language,
                                'google_product_id': google_product_ids})
                    if update_status:
                        done_count += 1
            else:
                self.shop_status = "done"
                message = "Well, it seems like your data is on vacation in the Land of Nowhere and having a grand old time sunbathing on the beaches of <b>No Information Island! </b>"
                return (0, 0, self.env['wk.wizard.message'].genrated_message(message, name="Export Alert: Oops, we're empty-handed!"))
        else:
            self.shop_status = "error"
            message = call_response['error']['message']
            raise UserError(_(message))
        return (total_product, done_count, error_msg)
    

    def _google_required_field_validation(self):

        field_mapping_lines = self.field_mapping_id.field_mapping_line_ids
        google_required_fields = self.env.cr.execute("""SELECT name FROM google_fields WHERE required = True""")
        google_required_fields_list = [f[0] for f in self.env.cr.fetchall()]
        mapped_fields = field_mapping_lines.mapped("google_field_id.name")
        missing_required_field_mapping = set(google_required_fields_list) - set(mapped_fields)
        return missing_required_field_mapping

    def button_export_product(self):

        # Basic Validation
        token_result = self.oauth_id.button_get_token(self.oauth_id)
        if token_result == "error":
            return self.env['wk.wizard.message'].genrated_message("Please check authorize your account...", name='Message')
        
        missing_mapping = self._google_required_field_validation()
        if missing_mapping:
            return self.env['wk.wizard.message'].genrated_message("%s Fields are required at google end but these are missing in field mapping"%(missing_mapping), name='Missing Mapping') 

        updation_type = "export"
        all_products_to_be_upload = []
        field_mapping_lines = self.field_mapping_id.field_mapping_line_ids
        mapped_product_details = self.env['product.mapping'].search(
            [('google_shop_id', '=', self.id)])
        error_product_details = mapped_product_details.filtered(
            lambda r: r.product_status == "error")
        error_products_product_ids = error_product_details.mapped(
            'product_id').ids
        mapped_products_product_ids = mapped_product_details.mapped(
            'product_id').ids
        error_products_mapped_ids = [(x.id, x.product_id.id)
                                     for x in error_product_details]
        JUNKMAPPING.extend(error_products_product_ids)
        product_ids = self.product_ids_domain_or_manual(
            mapped_products_product_ids, error_products_product_ids)
        context = self._context.copy()
        for rec in self.target_country_ids:
            
            context.update({'lang': rec.content_language.code,'target_country':rec.target_country,'content_language':rec.content_language,
                        'pricelist': self.product_pricelist_id.id, 'website_id': self.website_id.id, 'url_code': rec.content_language.url_code or self._default_website().default_lang_id.url_code})
            ids_to_export = list(set(product_ids)-set(mapped_products_product_ids))
            product_detail = self.with_context(context).get_product_detail(
                field_mapping_lines.ids, ids=ids_to_export)
            error_product_detail = self.with_context(context).get_product_detail(
                field_mapping_lines.ids, ids=error_products_product_ids)
            error_product_shop_link = []
            if error_product_detail:
                error_product_shop_link = [
                    y for x in error_products_mapped_ids for y in error_product_detail if (x[1] == y.get('id'))]
                product_detail += error_product_shop_link
            
            if len(ids_to_export) == 0 and len(error_product_shop_link) == 0:
                self.shop_status = "done"
                message = "Well, it seems like your data is on vacation in the Land of Nowhere and having a grand old time sunbathing on the beaches of<b> No Information Island! </b>"
                return self.env['wk.wizard.message'].genrated_message(message, name="Export Alert: Oops, we're empty-handed!")
            base_url = self.shop_url or self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            
            all_products_to_be_upload.extend(self.with_context(context).get_mapped_set(
                product_detail, field_mapping_lines, base_url=base_url, operation='insert'))
            # _logger()
            self.oauth_id.button_get_token(self.oauth_id)
        
        
        context.update({'lang': self.content_language.code,'target_country':self.target_country,'content_language':self.content_language,
                        'pricelist': self.product_pricelist_id.id, 'website_id': self.website_id.id, 'url_code': self.content_language.url_code or self._default_website().default_lang_id.url_code})
        ids_to_export = list(set(product_ids)-set(mapped_products_product_ids))
        ids_to_export = list(set(product_ids)-set(mapped_products_product_ids))
        product_detail = self.with_context(context).get_product_detail(
            field_mapping_lines.ids, ids=ids_to_export)
        error_product_detail = self.with_context(context).get_product_detail(
            field_mapping_lines.ids, ids=error_products_product_ids)
        error_product_shop_link = []
        
        if error_product_detail:
            error_product_shop_link = [
                y for x in error_products_mapped_ids for y in error_product_detail if (x[1] == y.get('id'))]
            product_detail += error_product_shop_link
        if len(ids_to_export) == 0 and len(error_product_shop_link) == 0:
            self.shop_status = "done"
            message = "There is nothing to export"
            return self.env['wk.wizard.message'].genrated_message(message, name='Message')
        base_url = self.shop_url or self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        all_products_to_be_upload.extend(self.with_context(context).get_mapped_set(
            product_detail, field_mapping_lines, base_url=base_url, operation='insert'))
        self.oauth_id.button_get_token(self.oauth_id)
       
        return self._manage_product_for_api(all_products_to_be_upload, context, updation_type)

    def manage_update_response_of_api(self, response, total_product, done_count):
        call_response = response.json()
        error_msg = ''
        if response.status_code == 401:
            self.shop_status = "error"
            message = "Account ID might had been expired so, refresh it and try again"
            raise UserError(_(message))
        elif response.status_code == 200:
            if 'entries' in call_response.keys():
                all_products_response = call_response['entries']
                for response in all_products_response:
                    
                    total_product += 1
                    target_country=self.env['res.country'].search([('code','=',response.get("product").get("targetCountry"))]).id
                    if self.target_country:
                        content_language=self.content_language.id
                    else:
                        content_language=country.content_language.id
                    if 'kind' and 'batchID' and 'product' in response.keys():
                        self.env['product.mapping'].search([('google_product_id', '=', response['product']['id']), ('google_shop_id', '=', self.id)]).write({
                            'update_status': True,
                            'product_status': 'updated',
                            'message': "Product id updated Successfully",
                            'google_product_id': response['product']['id']})
                        done_count += 1
                    else:
                        self.shop_status = "error"
                        product_id=self.env['product.product'].search([('default_code','=',response.get("product").get("offerId"))]).id
                        self.env['product.mapping'].search([('product_id.id', '=', product_id), ('google_shop_id', '=', self.id,('content_language', '=', content_language), ('target_country', '=', target_country))]).write({
                            'update_status': False,
                            'product_status': 'error',
                            'message': response['errors']['message'],
                            'google_product_id': None})
            else:
                self.shop_status = "done"
                message = "There is nothing to update"
                return (0, 0, self.env['wk.wizard.message'].genrated_message(message, name='Message'))
        else:
            self.shop_status = "error"
            message = call_response['error']['message']
            raise UserError(_(message))
        return (total_product, done_count, error_msg)

    def button_update_product(self, update_all_product=False):
        updation_type = "update"
        all_products_to_be_upload = []
        if update_all_product:
            updated_fields = self.env['product.mapping'].search(
                [('google_shop_id', '=', self.id), ('product_status', '=', 'updated')])
            operation_type = 'insert'
        else:
            token_result = self.oauth_id.button_get_token(self.oauth_id)
            if token_result == "error":
                return self.env['wk.wizard.message'].genrated_message("Please check authorize your account...", name='Message')
            if self.product_selection_type == 'domain':
                updated_fields = self.env['product.mapping'].search([('google_shop_id', '=', self.id), (
                    'update_status', '=', False), ('product_status', '=', 'updated')], limit=self.limit)
            else:
                manual_product_ids = self.product_ids_rel.ids
                updated_fields = self.env['product.mapping'].search([('google_shop_id', '=', self.id), (
                    'update_status', '=', False), ('product_status', '=', 'updated'), ('product_id', 'in', manual_product_ids)])
            operation_type = 'update'
        context = self._context.copy()
        for rec in updated_fields:
            context.update({'lang': rec.content_language.code,'target_country':rec.target_country,'content_language':rec.content_language,
                                'pricelist_id': self.product_pricelist_id.id, 'website_id': self.website_id.id, 'url_code': rec.content_language.url_code or self._default_website().default_lang_id.url_code})
            field_mapping_lines = self.field_mapping_id.field_mapping_line_ids
            updated_products_product_ids = rec.mapped('product_id').ids
            updated_products_mapped_ids = [
                (rec.id, rec.product_id.id)]
            updated_product_detail = self.with_context(context).get_product_detail(
                field_mapping_lines.ids, ids=updated_products_product_ids)
            updated_product_shop_link = [
                y for x in updated_products_mapped_ids for y in updated_product_detail if (x[1] == y.get('id'))]
            if len(updated_product_shop_link) == 0:
                self.shop_status = "done"
                message = "Our data elves searched high and low but <b>found no changes</b> to sprinkle their upgrade magic on. It's a quiet day in the land of updates!"
                return self.env['wk.wizard.message'].genrated_message(message, name='Update Alert!')
            base_url = self.shop_url or self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            all_products_to_be_upload.extend(self.with_context(context).get_mapped_set(
                updated_product_shop_link, field_mapping_lines, base_url=base_url, operation=operation_type))
     
        return self._manage_product_for_api(all_products_to_be_upload, context, updation_type)

    def get_product_detail(self, field_mapping_lines_ids, ids=[]):
        """
        !!!! -------- All the query that are executed executes here only
        """
        if not ids:
            return []
        field_mapping_model_ids = self.env['field.mapping.line'].search(
            [('id', 'in', field_mapping_lines_ids), ('field_type_value', '=', 'dynamic')]).mapped('model_field_id').ids
        field_mapping_model_name = self.env['ir.model.fields'].search(
            [('id', 'in', field_mapping_model_ids)]).mapped("name")
        field_mapping_model_name.append('product_tmpl_id')
        context = self._context.copy()
        context.update({'pricelist': self.product_pricelist_id.id,
                       'website_id': self.website_id.id})
        product_detail = self.env['product.product'].with_context(
            context).search_read([('id', 'in', ids)], field_mapping_model_name)
        return product_detail

    def call_google_insert_api(self, post_dict={}):
        if (self.oauth_id.authentication_state == 'authorize_token'):
            api_call_headers = {'Authorization': "Bearer " +
                                self.oauth_id.access_token, 'Content-Type': 'application/json'}
          
            api_call_response = requests.post(BATCHAPI,
                                              headers=api_call_headers, data=json.dumps(post_dict), verify=True, timeout=30)
            return api_call_response
        
    def _handle_field_mapping_line(self, product, field_mapping_lines, operation, product_id, product_detail, base_url, object_mapping_data={},target_country=''):
        for line in field_mapping_lines:

            google_field_id = line.google_field_id
            google_field_type = google_field_id.field_type
            key = google_field_id.name

            # Update operation doesn't support offerId and id 
            if (operation == 'update' and key in ['offerId', 'id']):
                    continue

            if google_field_type in ['string', 'boolean', 'list']:
                field_value = str()
                # Hook for imageLink and link
                if google_field_id.is_link_field:
                    self._handle_link_type_field(product_id, product, google_field_id.name, base_url,target_country)
                    continue

                # If mapped with fixed value
                if line.field_type_value == 'fixed':
                    field_value = line.fixed_text

                # mapping is a attribute type
                elif line.odoo_field_config == 'attribute':
                    if product_id.product_template_attribute_value_ids:
                        for attr in product_id.product_template_attribute_value_ids:
                            if attr.attribute_id.id == line.attribute_id.id:
                                field_value = attr.name
                                break

                else:
                    val = product_detail.get(line.model_field_id.name)
                    model_field_id = line.model_field_id
                    val = self._manage_selection_and_many2one_mapping(val, product_detail, model_field_id, key, product_id)
                    if val or line.default:
                        field_value = val or line.default
                product[key] = list(field_value) if google_field_type == 'list' else field_value

            elif google_field_type in ['object', 'list_object']:
                field_data = dict()
                property_field_mapping_id = line.property_field_mapping
                for prop in property_field_mapping_id:
                    property_key = prop.field_property_data_id.name.name
                    if prop.field_type in ['object', 'list_object']:
                        mapped_field_id = prop.field_mapping_line_id
                        mapped_field_name = mapped_field_id.google_field_id.name
                        field_data[mapped_field_name] = list(object_mapping_data.get(mapped_field_name)) if prop.field_type == 'list_object' else object_mapping_data.get(mapped_field_name)
                    else:
                        if prop.odoo_field_id:
                            val = product_detail.get(prop.odoo_field_id.name) or getattr(product_id, prop.odoo_field_id.name)
                            if prop.odoo_field_id.ttype in ["selection", "many2one"]:
                                val = self._manage_selection_and_many2one_mapping(val, product_detail, prop.odoo_field_id, property_key, product_id)
                        else:
                            val = prop.default_value
                        if prop.field_type == "number":
                            val = int(val)
                        field_data[property_key] = [val] if prop.field_type == 'list' else val
                if google_field_type == 'list_object':
                    key_data = product.get(key, False)
                    if key_data:
                        key_data.append(field_data)
                    else:
                        product[key] = [field_data]
                else:
                    product[key] = field_data

        
    def _handle_link_type_field(self, product_id, product, field_name, base_url,target_country=''):
        prod_temp_ref = self.env['product.template']
        if field_name == "imageLink":
            product['imageLink'] = "%s/web/image/product.product/%s/image_1024" % (
                    base_url, product_id.id)
        elif field_name == "additionalImageLinks":
            attachments = self.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'product.template'),
                ('res_id', '=', product_id.product_tmpl_id.id),
                ('mimetype', 'ilike', 'image'),
                ('res_field', '!=', 'image_1920'),
            ])
            if attachments:
                for att in attachments:
                    if not att.public:
                        att.public = True
                product['additionalImageLinks'] = [
                    "%s/web/image/%s/image_1024" % (base_url, att.id)
                    for att in attachments
                ]
        elif field_name == "link":
            
            product['shipping'] = [
                {
                "country": target_country,
                "service": "Standard",
                },
               
                ],
        
            #product['link'] = base_url+'/'+target_country+'/'+self._context.get('url_code', 'en')+"/shop/product/"+slug(
            product['link'] = base_url + '/shop/product/' + slug(
                prod_temp_ref.search([('id', '=', product_id.product_tmpl_id.id)], limit=1))
        else:
            raise UserError("%s is not support url link type value"%(field_name))
        

    def _handle_selection_type_field(self, model_field_id, product_id):
        prod_temp_ref = self.env['product.template']
        return dict(prod_temp_ref._fields[model_field_id.name].selection).get(
                                product_id.mapped(model_field_id.name)[0])
    
    def _handle_many2one_type_field(self, val):
        if isinstance(val,list) or isinstance(val,tuple):
            return val[1] if val else False
        return val.name
    
    def _manage_selection_and_many2one_mapping(self, val, product_detail, model_field_id, key, product_id):
        
        if model_field_id.ttype == "selection":
            if key == 'googleProductCategory':
                val = int(product_detail.get(
                    model_field_id.name)) if model_field_id.name == 'google_shop_product_categ' else False
            else:
                val = self._handle_selection_type_field(model_field_id, product_id)
        
        elif model_field_id.ttype in ["many2one"]:
            val = self._handle_many2one_type_field(val)
        return val
    
    

    def get_mapped_set(self, product_set, field_mapping_lines, base_url, operation):

        # try:
            target_country=self._context.get('target_country')
            content_language=self._context.get('content_language')               
            object_type_mapping = self.env['field.mapping.line'].search([('field_mapping_type','=','object_field_mapping')])  

            object_mapping_data = dict()
        
            # Generator Method to get value on fly
            def get_product_data(seq):
                yield product_set[seq]

            product_batch_data_list = []
            product_set_len = len(product_set)
            for seq in range (0, product_set_len):
                product_detail = next(get_product_data(seq))

                # Product Dict
                product = dict()

                if operation == 'insert':
                    product_batch_data = {
                        "method": "insert",
                        'product': {}
                    }
                    product['targetCountry'] = target_country.code
                    product['channel'] = self.channel
                    product['contentLanguage'] = content_language.iso_code.split('_')[0]
                else:
                    product_batch_data = {
                        "method": "update",
                        'product': {}
                    }
                    product_id = self.env['product.mapping'].search(
                        [('product_id.id', '=', product_detail.get('id')), ('google_shop_id', '=', self.id),
                         ('target_country','=',target_country.id),('content_language','=',content_language.id)])
                    product_batch_data['productId'] = product_id[0].google_product_id

                # Primary data for API
                product_batch_data['merchantId'] = self.merchant_id
                product_batch_data['batchId']=int(str(product_detail.get('id'))+str(target_country.id)+str(content_language.id))
                if content_language.code==self.content_language.code and target_country.id==self.target_country.id :
                    product_batch_data['batchId'] = product_detail.get('id')
            

                # Browse Product
                product_id = self.env['product.product'].search(
                    [('id', '=', product_detail.get('id'))])
                

                # Product Expiry Hook
                if product_id.is_published:
                    datetime_utc = datetime.now(UTC)+timedelta(days=30)
                    product['expiration_date'] = datetime_utc.strftime(
                        '%Y-%m-%dT%H:%M%z')
                else:
                    datetime_utc = datetime.now(UTC)
                    product['expiration_date'] = datetime_utc.strftime(
                        '%Y-%m-%dT%H:%M%z')
                pricelist = self.product_pricelist_id

                self._handle_field_mapping_line(object_mapping_data, object_type_mapping, operation, product_id, product_detail, base_url,target_country.code)
                self._handle_field_mapping_line(product, field_mapping_lines, operation, product_id, product_detail, base_url, object_mapping_data,target_country.code)

                self._balance_price_and_saleprice(product, product_id, pricelist)

                product_batch_data.update({'product': product})
                product_batch_data_list.append(product_batch_data)
            return product_batch_data_list
        # except Exception as e:
        #     raise UserError(e)
    
    def _balance_price_and_saleprice(self, product, product_id, pricelist):

        # Managing pricelist price
        price_info = pricelist._get_product_price(product_id, 1)
        p_d = product.get('price')
        saleprice = product.get('salePrice').get('value') if product.get('salePrice').get('value') < price_info else price_info
        price = p_d.get('value')
        price = self._calculate_tax_included_price(product_id, price)
        saleprice = self._calculate_tax_included_price(product_id, saleprice)
        if saleprice > price:
            product.get('salePrice').update({'value':price})
            product.get('Price').update({'value':saleprice})
        else:
            product.get('price').update({'value':price})
            product.get('salePrice').update({'value':saleprice})
    
    def _calculate_tax_included_price(self, product_id, price):
        return product_id.product_tmpl_id.taxes_id.compute_all(price, product=product_id.product_tmpl_id, partner=self.env['res.partner']).get('total_included')

    def button_authorize_merchant(self):
        if self.merchant_id:
            api_call_response = {}
            token_result = self.oauth_id.button_get_token(self.oauth_id)
            if token_result == "error":
                return self.env['wk.wizard.message'].genrated_message("Please check authorize your account...", name='Message')
            try:
                api_call_headers = {
                    'Authorization': "Bearer "+self.oauth_id.access_token}
                api_call_response = requests.get(AUTHAPI+self.merchant_id +
                                                 '/accounts/'+self.merchant_id, headers=api_call_headers, verify=True, timeout=30)       
                _logger.info(
                    "Response status of the Auth Token and Merchant ID :- %r", api_call_response.status_code)
                
                response_dict = json.loads(api_call_response.text)
                if api_call_response.status_code != 200:
                    message = response_dict.get("error",False)
                    self.error_log("Authentication Error", message)
                    return self.env['wk.wizard.message'].genrated_message(message, name='Message')
                else:
                    self.shop_status = 'validate'
            except:
                message = "Please Go to Account in setting and generate account token first"
                return self.env['wk.wizard.message'].genrated_message(message, name='Message')
        else:
            raise UserError(
                "Please enter the merchant ID in the account Section first")

    @api.constrains('channel', 'target_country', 'content_language', 'website_id')
    def _criteria(self):
        for record in self:
            same_record = record.search(
                [
                    ('channel', '=', record.channel),
                    ('target_country', '=', record.target_country.id),
                    ('content_language', '=', record.content_language.id),
                    ('website_id', '=', record.website_id.id)
                 ]
            ).ids

            if len(same_record) > 1:
                raise ValidationError(_('Same Shop Exists in Database'))

    # -------------------------------------------------------------------------
    # TOKEN STATUS
    # -------------------------------------------------------------------------
    def get_token_status(self):
        return self.oauth_id.button_get_token(self.oauth_id)

    def open_product_mapping_view(self):
        mappings = self.env['product.mapping'].search(
            [('google_shop_id', '=', self.id)]).ids
        action = self.env.ref(
            'google_shop.product_mapping_action_button_click').read()[0]
        action['domain'] = [('id', 'in', mappings)]
        return action

    def unlink(self):
        for rec in self:
            if rec.mapping_count <= 0:
                super(GoogleMerchantShop, rec).unlink()
            else:
                raise UserError(
                    "Firstly Delete all the mappings then the shop will be deleted")

    def _mapping_count(self):
        for rec in self:
            rec.mapping_count = self.env['product.mapping'].search_count(
                [('google_shop_id', '=', rec.id)])

    def button_delete_product_link(self):
        oauth2_error, error_count, done_count = 0, 0, 0

        mapping_ref = self.env['product.mapping'].search(
            [('google_shop_id', '=', self.id)])

        if len(mapping_ref) == 0:
            self.shop_status = "done"
            message = "There is nothing to delete"
            return self.env['wk.wizard.message'].genrated_message(message, name='Message')

        if mapping_ref:
            oauth2_error, error_count, done_count = mapping_ref.unlink()

        elif oauth2_error > 0:
            self.shop_status = "error"
            message = "Account ID might had been expired so, refresh it and try again"
            return self.env['wk.wizard.message'].genrated_message(message, name='Message')
        elif error_count > 0 or done_count > 0:
            total_product = done_count+error_count
            if error_count > 0:
                self.shop_status = "error"
            else:
                self.shop_status = "new"
            message = ("{0} out of {1} products are deleted".format(
                done_count, total_product))
            self.message_post(body=Markup(message))
            return self.env['wk.wizard.message'].genrated_message(message, name='Message')

    def button_show_debug_wizard(self):
        context = {'google_shop': self.id}
        return self.env['google.shop.debug'].with_context(context).genrated_wizard()
