# PakMart OneLake Upload Pipeline — Configuration & Setup Guide

This guide walks you through every step needed to configure the `.env` file,
find each required value in Azure and Microsoft Fabric, and set up an
On-Premises Data Gateway when your machine is behind a corporate network or
firewall.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Copy and open the .env file](#2-copy-and-open-the-env-file)
3. [AUTH_METHOD — choosing how to authenticate](#3-auth_method--choosing-how-to-authenticate)
4. [AZURE_TENANT_ID — finding your Tenant ID](#4-azure_tenant_id--finding-your-tenant-id)
5. [AZURE_CLIENT_ID & AZURE_CLIENT_SECRET — creating a Service Principal](#5-azure_client_id--azure_client_secret--creating-a-service-principal)
6. [FABRIC_WORKSPACE_ID — finding your Workspace ID](#6-fabric_workspace_id--finding-your-workspace-id)
7. [FABRIC_LAKEHOUSE_ID — finding your Lakehouse ID](#7-fabric_lakehouse_id--finding-your-lakehouse-id)
8. [LOCAL_DATA_ROOT — pointing to your generated data](#8-local_data_root--pointing-to-your-generated-data)
9. [Tuning upload behaviour](#9-tuning-upload-behaviour)
10. [Completed .env example](#10-completed-env-example)
11. [Verify the configuration (dry run)](#11-verify-the-configuration-dry-run)
12. [On-Premises Data Gateway — when and why](#12-on-premises-data-gateway--when-and-why)
13. [Installing the On-Premises Data Gateway](#13-installing-the-on-premises-data-gateway)
14. [Connecting the gateway to Fabric](#14-connecting-the-gateway-to-fabric)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Prerequisites

Before you start, make sure you have:

- [ ] A **Microsoft Fabric** workspace (free trial or paid capacity)
- [ ] A **Lakehouse** created inside that workspace
- [ ] **Python 3.9+** installed on your machine
- [ ] Dependencies installed:
  ```bash
  python -m pip install -r requirements.txt
  ```
- [ ] An **Azure Active Directory** account with at least one of:
  - Permission to create App Registrations (for service principal auth), **or**
  - A personal login to the Fabric tenant (for device code / CLI auth)

---

## 2. Copy and open the .env file

The pipeline reads credentials from a `.env` file that lives in the
`onelake_upload/` folder. It is **never committed to source control** —
`.env` is already in `.gitignore` by convention.

```bash
# From the onelake_upload/ folder:
copy .env.template .env
```

Then open `.env` in any text editor (Notepad, VS Code, etc.) and fill in
each value as described in the sections below.

---

## 3. AUTH_METHOD — choosing how to authenticate

```dotenv
AUTH_METHOD=service_principal
```

| Value | When to use | Extra vars needed |
|---|---|---|
| `service_principal` | CI/CD, scheduled tasks, production — **recommended** | `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| `device_code` | First-time setup, interactive developer use — opens a browser | `AZURE_TENANT_ID` only |
| `cli` | You already ran `az login` in this terminal session | None |

> **Quickest start for a developer:** use `device_code` — no app registration
> needed. Just run the script and it prints a URL + code to paste in the browser.

---

## 4. AZURE_TENANT_ID — finding your Tenant ID

Your **Tenant ID** is the GUID that identifies your Azure Active Directory
(Entra ID) organisation. It looks like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`.

### Method A — Azure Portal

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Search **"Microsoft Entra ID"** in the top search bar and click it
3. On the **Overview** page, copy the **Tenant ID** field

```
Azure Portal → Microsoft Entra ID → Overview → Tenant ID
```

### Method B — Microsoft Fabric URL

When you are logged into Fabric, look at the URL:
```
https://app.fabric.microsoft.com/home?experience=power-bi
```
Click your profile picture (top right) → **About Microsoft Fabric** →
the dialog shows your **Tenant ID**.

### Method C — Azure CLI

```bash
az account show --query tenantId -o tsv
```

Paste the result into your `.env`:
```dotenv
AZURE_TENANT_ID=3d7b2a0e-1234-5678-abcd-ef0123456789
```

---

## 5. AZURE_CLIENT_ID & AZURE_CLIENT_SECRET — creating a Service Principal

A **Service Principal** is an application identity that your script uses to
authenticate programmatically — no human login required.

> Skip this section if you are using `AUTH_METHOD=device_code` or
> `AUTH_METHOD=cli`.

### Step 1 — Register a new application

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Navigate to **Microsoft Entra ID → App registrations → New registration**
3. Fill in:
   - **Name:** `PakMart OneLake Uploader` (or any name you like)
   - **Supported account types:** _Accounts in this organisational directory only_
   - **Redirect URI:** leave blank
4. Click **Register**
5. Copy the **Application (client) ID** — this is your `AZURE_CLIENT_ID`

```
Entra ID → App registrations → <your app> → Overview
  Application (client) ID  ← copy this
```

### Step 2 — Create a client secret

1. On the same app page, go to **Certificates & secrets → Client secrets → New client secret**
2. Set a description (e.g. `pakmart-pipeline`) and an expiry (12 or 24 months)
3. Click **Add**
4. **Copy the secret Value immediately** — it is only shown once

```dotenv
AZURE_CLIENT_ID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
AZURE_CLIENT_SECRET=AbC~1dEfGhIjKlMnOpQrStUvWxYz.0123456789
```

> **Security tip:** rotate the secret before the expiry date and update `.env`.

### Step 3 — Grant the Service Principal access to OneLake

The service principal needs **Contributor** (or higher) access to the Fabric
workspace so it can write files to OneLake.

1. In Microsoft Fabric, open your **Workspace**
2. Click the **three dots (…) → Manage access**
3. Click **Add people or groups**
4. Type the **display name** of your app registration (e.g. `PakMart OneLake Uploader`)
5. Set the role to **Contributor** (minimum needed to upload files)
6. Click **Add**

```
Fabric → Workspace → … → Manage access → Add → <app name> → Contributor
```

---

## 6. FABRIC_WORKSPACE_ID — finding your Workspace ID

The Workspace ID is the GUID segment in the Fabric URL when you have a
workspace open.

### Method A — from the browser URL

1. Open [https://app.fabric.microsoft.com](https://app.fabric.microsoft.com)
2. Click on your workspace in the left sidebar
3. Look at the browser URL — it contains the workspace GUID:

```
https://app.fabric.microsoft.com/groups/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/...
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                         This is your FABRIC_WORKSPACE_ID
```

### Method B — from Workspace Settings

1. Inside your workspace, click the **gear icon → Workspace settings**
2. Under the **General** tab, scroll to the bottom
3. Copy the **Workspace ID** field

```dotenv
FABRIC_WORKSPACE_ID=12345678-abcd-ef01-2345-6789abcdef01
```

---

## 7. FABRIC_LAKEHOUSE_ID — finding your Lakehouse ID

### Method A — from the browser URL

1. Open your workspace in Fabric
2. Click on your **Lakehouse** to open it
3. The URL now contains both IDs:

```
https://app.fabric.microsoft.com/groups/<workspace_id>/lakehouses/<lakehouse_id>
                                                                    ^^^^^^^^^^^^
                                                                    copy this
```

### Method B — from the Lakehouse properties

1. In the workspace item list, **right-click** (or click **…**) on your Lakehouse
2. Select **Properties**
3. Copy the **ID** shown in the dialog

```dotenv
FABRIC_LAKEHOUSE_ID=aabbccdd-1122-3344-5566-778899aabbcc
```

> **Creating a Lakehouse if you don't have one yet:**
> In your Fabric workspace → **New → Lakehouse** → give it a name
> (e.g. `pakmart_bronze`) → Create.

---

## 8. LOCAL_DATA_ROOT — pointing to your generated data

This is the path to the `pakmart_data/` folder produced by the generator.

```dotenv
# Relative path (when running from inside onelake_upload/)
LOCAL_DATA_ROOT=../pakmart_data

# Absolute path (Windows — use forward slashes or double backslashes)
LOCAL_DATA_ROOT=F:/siddi/msfabric_retails_data/pakmart_data
```

The pipeline expects this structure inside the folder:
```
pakmart_data/
├── full/
│   ├── dimension_city/
│   ├── dimension_customer/
│   ├── dimension_date/
│   ├── dimension_employee/
│   ├── dimension_stock_item/
│   └── fact_sale/
└── incremental/
    └── fact_sale_1y_incremental/
```

If the folder doesn't exist yet, run the data generator first:
```bash
cd ..
python pakistani_retail_data_generator.py
```

---

## 9. Tuning upload behaviour

These values have sensible defaults. Only change them if you have a specific
reason.

| Variable | Default | What it controls |
|---|---|---|
| `ONELAKE_ENDPOINT` | `https://onelake.dfs.fabric.microsoft.com` | OneLake DFS URL — leave as-is unless Microsoft changes it |
| `MAX_WORKERS` | `6` | Parallel upload threads. Increase to 8–12 on a fast connection; lower to 2–3 on a slow or metered link |
| `CHUNK_SIZE` | `4194304` (4 MB) | Size of each upload chunk in bytes. Larger = fewer round trips but more memory. Keep between 1 MB and 16 MB |
| `MAX_RETRIES` | `3` | How many times to retry a failed file before giving up |
| `RETRY_BACKOFF` | `2` | Exponential back-off base (seconds). Attempt 1 waits 2s, attempt 2 waits 4s, attempt 3 waits 8s |
| `SKIP_UNCHANGED` | `True` | Skip uploading if remote file size matches local. Set to `False` to always overwrite |

---

## 10. Completed .env example

Below is a filled-in example (all values are fictional):

```dotenv
AUTH_METHOD=service_principal

AZURE_TENANT_ID=3d7b2a0e-aaaa-bbbb-cccc-ef0123456789
AZURE_CLIENT_ID=ffffffff-1111-2222-3333-444444444444
AZURE_CLIENT_SECRET=xYz~9AbCdEfGhIjKlMnOpQrStUv.0123456789

FABRIC_WORKSPACE_ID=12345678-abcd-ef01-2345-6789abcdef01
FABRIC_LAKEHOUSE_ID=aabbccdd-1122-3344-5566-778899aabbcc

ONELAKE_ENDPOINT=https://onelake.dfs.fabric.microsoft.com

LOCAL_DATA_ROOT=../pakmart_data

MAX_WORKERS=6
CHUNK_SIZE=4194304
MAX_RETRIES=3
RETRY_BACKOFF=2
SKIP_UNCHANGED=True
```

---

## 11. Verify the configuration (dry run)

Before uploading anything, run a dry-run to confirm every path resolves:

```bash
# From the onelake_upload/ folder
python main.py --mode full --dry-run
```

Expected output:
```
[DRY RUN]  mode=full  tables=None  years=None
  LOCAL FILE                                              REMOTE PATH
  -----------------------------------------------------------------------
  ..\pakmart_data\full\dimension_city\dimension_city.csv  full/dimension_city/dimension_city.csv
  ...
  Total: 9 file(s) would be uploaded.
```

Then do a real upload of just one small file to confirm credentials work:

```bash
python main.py --mode table:dimension_city
```

If that succeeds, run the full load:

```bash
python main.py --mode full
```

---

## 12. On-Premises Data Gateway — when and why

An **On-Premises Data Gateway** is a Windows service that acts as a bridge
between your local machine (or corporate network) and Microsoft cloud
services (Fabric, Power BI, Power Automate).

You need it when:

| Scenario | Need gateway? |
|---|---|
| Your `pakmart_data` folder is on a machine **inside a corporate network** that blocks direct outbound HTTPS to `*.dfs.fabric.microsoft.com` | **Yes** |
| You want **Power BI / Fabric pipelines** to pull data from an on-premises SQL Server, file share, or local folder | **Yes** |
| You want **scheduled refresh** of a Fabric semantic model that points to an on-premises source | **Yes** |
| You are uploading from a personal laptop with direct internet access | No — the Python uploader connects directly |
| You are running the uploader from an Azure VM or GitHub Actions | No — already in the cloud |

> **For the Python uploader specifically:** the script talks directly to
> OneLake over HTTPS port 443. If that port is **open** on your network,
> you do **not** need a gateway. The gateway is only needed when cloud
> services need to call **back** to your on-premises resources, or when
> your firewall blocks the direct connection.

### Gateway types

| Type | Use case |
|---|---|
| **Standard mode** | Shared gateway — multiple users and services can use it; installed as a Windows service; recommended for production |
| **Personal mode** | Single user, no sharing; useful for quick dev/test; cannot be used for scheduled refresh in a shared workspace |

---

## 13. Installing the On-Premises Data Gateway

### Step 1 — Download the installer

1. Go to [https://aka.ms/opdg](https://aka.ms/opdg) (Microsoft's official gateway download page)
   or in Fabric: **Settings (gear icon) → Manage gateways → Download gateway**
2. Download the **On-premises data gateway** installer (not the personal mode version)
3. Run the installer on a **Windows machine that is always on** (a server or a desktop that is not shut down)

> System requirements:
> - Windows 10 / Windows Server 2012 R2 or later
> - .NET Framework 4.7.2+
> - 8 GB RAM recommended
> - Stable internet connection (the gateway only needs **outbound** HTTPS 443)

### Step 2 — Sign in during installation

1. When the installer asks you to sign in, use the **same Microsoft 365 / Azure AD account** that owns the Fabric workspace
2. Choose **Register a new gateway on this computer**
3. Give it a name (e.g. `PakMart-Gateway-Prod`) and a recovery key — **save the recovery key somewhere safe**
4. Click **Configure**

### Step 3 — Verify the gateway is running

After installation, the **On-premises data gateway** app opens automatically.
The status should show a green checkmark:

```
✔  The gateway PakMart-Gateway-Prod is online and ready to be used.
```

The gateway runs as a Windows service called `On-premises data gateway service`.
You can verify it in **Services** (`services.msc`) — it should be set to
**Automatic (Delayed Start)**.

---

## 14. Connecting the gateway to Fabric

### In Microsoft Fabric

1. Open Fabric → **Settings (gear icon) → Manage connections and gateways**
2. Under **On-premises data gateways**, you should see your newly installed gateway listed
3. Click **…** next to it → **Settings** to configure allowed users

### Creating a gateway connection (for Fabric pipelines / Data Factory)

If you want a **Fabric Data Pipeline** (not the Python uploader) to read
files from your local machine through the gateway:

1. In **Manage connections and gateways → New connection**
2. Choose **On-premises**
3. Select your gateway from the dropdown
4. Choose **Connection type** = **File System**
5. Set the **Root folder path** to where your `pakmart_data/` folder is stored, e.g.:
   ```
   F:\siddi\msfabric_retails_data\pakmart_data
   ```
6. Set **Authentication method** = Windows (or Anonymous for a local path)
7. Click **Create**

You can then reference this connection from a **Copy Data** activity in a
Fabric pipeline to read the CSVs directly without running the Python script.

### Proxy / firewall settings for the gateway

If your corporate firewall requires a proxy:

1. Open the gateway app → **Network** tab
2. Enable **Use a proxy** and enter your proxy address and credentials
3. Ensure the following **outbound** endpoints are whitelisted on your firewall:

| Endpoint | Port | Purpose |
|---|---|---|
| `*.servicebus.windows.net` | 443 / 5671–5672 | Gateway ↔ Azure Service Bus relay |
| `*.frontend.clouddatahub.net` | 443 | Gateway ↔ Power BI |
| `*.analysis.windows.net` | 443 | Analysis Services |
| `login.microsoftonline.com` | 443 | Azure AD authentication |
| `*.dfs.fabric.microsoft.com` | 443 | OneLake DFS endpoint |
| `*.blob.core.windows.net` | 443 | Azure Blob storage |

---

## 15. Troubleshooting

### `EnvironmentError: Required environment variable 'AZURE_TENANT_ID' is not set`

Your `.env` file is missing or the variable is empty.

- Check that `.env` exists in the `onelake_upload/` folder (not just `.env.template`)
- Open it and confirm the value is filled in (no placeholder text)
- Make sure there are **no quotes** around the value: `AZURE_TENANT_ID=abc...` not `AZURE_TENANT_ID="abc..."`

---

### `ClientAuthenticationError: AADSTS700016: Application not found in directory`

The `AZURE_CLIENT_ID` does not exist in the tenant identified by `AZURE_TENANT_ID`.

- Double-check you copied the **Application (client) ID**, not the **Object ID**
- Confirm the app registration is in the same tenant as your Fabric workspace

---

### `HttpResponseError: 403 AuthorizationPermissionMismatch`

The service principal authenticated successfully but does not have write
access to the OneLake filesystem.

- In Fabric, go to your workspace → **Manage access**
- Confirm the app registration appears with the **Contributor** role (or higher)
- Wait 2–3 minutes after granting access — AAD role propagation can be slow

---

### `HttpResponseError: 404 FilesystemNotFound`

`FABRIC_WORKSPACE_ID` or `FABRIC_LAKEHOUSE_ID` is wrong.

- Re-check both GUIDs using the methods in sections 6 and 7
- Confirm the Lakehouse actually exists — open Fabric and verify

---

### Upload is very slow

- Increase `MAX_WORKERS` to 8 or 10 in `.env`
- Check if your ISP is throttling traffic to `*.dfs.fabric.microsoft.com`
- For large files, try increasing `CHUNK_SIZE` to `8388608` (8 MB)

---

### Gateway shows as offline in Fabric

1. Open **Services** (`Win + R` → `services.msc`)
2. Find **On-premises data gateway service**
3. Right-click → **Restart**
4. Return to Fabric → **Manage connections and gateways** → refresh the page

If it still shows offline, check the gateway logs at:
```
C:\Windows\ServiceProfiles\PBIEgwService\AppData\Local\Microsoft\On-premises data gateway\
```

---

### `device_code` auth — token expired

The device code flow gives you a short-lived code (15 minutes). If the
upload takes longer than that to start, the token will have been refreshed
automatically by the SDK. If you see an expiry error, simply re-run the
command — the SDK will prompt for a new code.

---

*Last updated: generated for PakMart Traders MS Fabric project.*
