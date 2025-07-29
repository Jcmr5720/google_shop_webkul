# Google Shopping Feed (google_shop)

## Overview

The Odoo Google Shopping Feed Module is intended to enable you to create product feeds on Odoo with your Google Merchant Center, allowing you to send product information from Odoo to your Google Merchant account.
Additionally, map the Odoo Product fields to the Google fields in order on the product price, description, and so on to appear correctly on Google Shopping. Originally, the service listed merchant-submitted prices and was monetized through AdWords advertising, similar to other Google services. Nevertheless, Google announced in late 2012 that the service would transition to a paid model in which merchants would have to pay the company to list their products on the service.

### Features:
- Multi-Country and Multi-Language Support
-  Introduce Dry Run Functionality and Product Tax Management
- Check Merchant Product Status in Odoo
- Fetch Product's Status in Bulk From Merchant Account
- Integrate GMC With Odoo
- One-Step Domain Verification With Google
- Manage Product Prices With Odoo Pricelist
- Upload Product Data To GMC
- Map Product Categories
- Update product mapping status manually from Odoo backend
- Map Product Fields
- Map Product Attributes field on Google Merchant Center
- Add admin email id to notify on OAuth token expiration
- Delete products from the local and merchant centers simultaneously
- Display real traffic metrics (clicks, impressions and CTR) for mapped products
  using Google Merchant Center reports

## Prerequisites

Before installing this module, you need to install the **`wk_wizard_messages`** module, as this module provides wizards to show a message.

- **Odoo Version**: 16
- **Dependencies**: `wk_wizard_messages`

## Configuration

### Step 1: Generate Token

1. Navigate to **Account** in the Odoo backend.
2. Under the **Account** section, Add Client Id, Client Secret and Merchent Id.


### Step 2:Create Google shop Account

1. Navigate to **google shops** in the Odoo backend.
2. Under the **shop** section

### Step 3: Create a field mpping

1. Navigate to **mapping** in the Odoo backend.
2. Under the **field mapping** section, 

### Step 4: Token expiry notification through mail

1. Navigate to **configuration** in the Odoo backend.
2. Under the **Google Shop Feed * section set email to send notification, 


## Additional Notes
    To create Google developer console account  link (https://console.cloud.google.com/welcome?inv=1&invt=AbmHRg&project=norse-appliance-424105-g5)

    To create Google Merchant Center account link (https://merchants.google.com/)

## Credits
    Author: Webkul Software Pvt. Ltd.

