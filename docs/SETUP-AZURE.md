# Setup Guide: Microsoft Entra ID + Azure Bot Registration

This guide walks through the two manual Azure/Microsoft steps needed to complete the Teams RAG Chatbot.

---

## Part 1: Microsoft Entra ID App Registration (for SharePoint access)

The SharePoint sync Lambda uses Microsoft Graph API to read documents. You need an Entra ID app registration with the right permissions.

### Steps

1. **Go to** [Microsoft Entra admin center](https://entra.microsoft.com/)

2. **Navigate to** *Identity → Applications → App registrations → New registration*

3. **Register the app:**
   - Name: `teams-rag-chatbot-sharepoint-sync`
   - Supported account types: *Accounts in this organizational directory only (Single tenant)*
   - Redirect URI: Leave blank
   - Click **Register**

4. **Note these values** (you'll need them for Terraform):
   - **Application (client) ID** → this is `sharepoint_client_id`
   - **Directory (tenant) ID** → this is `sharepoint_tenant_id`

5. **Add API permissions:**
   - Go to *API permissions → Add a permission*
   - Select **Microsoft Graph → Application permissions**
   - Search for and add: `Sites.Read.All`
   - Click **Grant admin consent for your organization** (requires admin rights)

6. **Create a client secret:**
   - Go to *Certificates & secrets → New client secret*
   - Description: `teams-rag-chatbot`
   - Expiry: 24 months
   - Click **Add**
   - **Copy the Value immediately** → this is `sharepoint_client_secret`

### Deploy to Terraform

Set the variables before running `terraform apply`:

```powershell
$env:TF_VAR_sharepoint_tenant_id = "<your-tenant-id>"
$env:TF_VAR_sharepoint_client_id = "<your-client-id>"
$env:TF_VAR_sharepoint_client_secret = "<your-client-secret>"
```

---

## Part 2: Azure Bot Registration (for Teams channel)

The bot needs an Azure Bot Service registration to communicate with Microsoft Teams.

### Prerequisites
- An Azure subscription (your tenant likely already has one)
- If not, create a free Azure account at [azure.microsoft.com](https://azure.microsoft.com/)

### Steps

1. **Go to** [Azure Portal](https://portal.azure.com/)

2. **Create a new Bot resource:**
   - Search for *Azure Bot* → Click **Create**
   - Bot handle: `teams-rag-chatbot`
   - Subscription: Select your subscription
   - Resource group: Create new → `rg-teams-rag-chatbot`
   - Pricing tier: **F0 (Free)** — 10,000 messages/month
   - Type of app: **Single Tenant**
   - Creation type: **Create new Microsoft App ID**
   - Click **Review + Create → Create**

3. **Get the App ID and Password:**
   - After creation, go to the bot resource
   - Click **Configuration** in the left sidebar
   - Copy the **Microsoft App ID**
   - Click **Manage Password** → **New client secret** → Copy the **Value**

4. **Set the messaging endpoint:**
   - Still in Configuration, set **Messaging endpoint** to:
   ```
   https://qqx9id5oga.execute-api.us-east-1.amazonaws.com/api/messages
   ```
   - Click **Apply**

5. **Enable the Teams channel:**
   - Go to **Channels** in the left sidebar
   - Click **Microsoft Teams**
   - Accept the terms → Click **Apply**

6. **Test in Teams:**
   - Go to **Channels → Microsoft Teams → Open in Teams**
   - This opens a chat with your bot — try sending a question!

### Deploy credentials to Terraform

```powershell
$env:TF_VAR_bot_app_id = "<your-app-id>"
$env:TF_VAR_bot_app_password = "<your-app-password>"
$env:TF_VAR_db_master_password = 'EricisAwes0me!23'
terraform apply
```

This updates the Secrets Manager secret so the Lambda can validate Bot Framework tokens.

---

## Quick Reference

| Variable | Where to find it |
|---|---|
| `sharepoint_tenant_id` | Entra ID → App registrations → Directory (tenant) ID |
| `sharepoint_client_id` | Entra ID → App registrations → Application (client) ID |
| `sharepoint_client_secret` | Entra ID → Certificates & secrets → Client secret Value |
| `bot_app_id` | Azure Portal → Bot resource → Configuration → Microsoft App ID |
| `bot_app_password` | Azure Portal → Bot resource → Configuration → Manage Password |
