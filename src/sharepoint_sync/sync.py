"""
SharePoint-to-S3 Sync Lambda

Pulls documents from a SharePoint Online document library using Microsoft Graph API
and uploads them to S3 for Bedrock Knowledge Base ingestion.

Runs on a schedule (EventBridge) or can be invoked manually.
"""
import json
import logging
import os
import tempfile
from datetime import datetime

import boto3
import msal
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
secretsmanager = boto3.client("secretsmanager")

BUCKET_NAME = os.environ["DOCUMENTS_BUCKET"]
SHAREPOINT_SECRET_ARN = os.environ["SHAREPOINT_SECRET_ARN"]
SHAREPOINT_SITE_URL = os.environ["SHAREPOINT_SITE_URL"]

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

# File extensions Bedrock KB can process
SUPPORTED_EXTENSIONS = {
    ".pdf", ".txt", ".md", ".html", ".htm",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".csv", ".json", ".xml",
}

# Folders to skip during sync (case-insensitive prefix match)
EXCLUDED_FOLDERS = {
    "tools/scoutsuite-master",
    "azure invoices",
    "aws invoices",
}


def handler(event, context):
    """Lambda handler — sync SharePoint docs to S3, then trigger ingestion."""
    logger.info("Starting SharePoint-to-S3 sync")

    # Get SharePoint credentials from Secrets Manager
    creds = get_sharepoint_credentials()

    # Authenticate with Microsoft Graph API
    access_token = authenticate(creds)

    # Get the SharePoint site and drive
    site_id = get_site_id(access_token)
    drive_id = get_default_drive_id(access_token, site_id)

    # List and sync all files
    synced, skipped, failed = sync_files(access_token, drive_id, site_id)

    logger.info(f"Sync complete: {synced} synced, {skipped} skipped, {failed} failed")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "synced": synced,
            "skipped": skipped,
            "failed": failed,
        }),
    }


def get_sharepoint_credentials():
    """Retrieve SharePoint OAuth credentials from Secrets Manager."""
    response = secretsmanager.get_secret_value(SecretId=SHAREPOINT_SECRET_ARN)
    return json.loads(response["SecretString"])


def authenticate(creds):
    """Authenticate with Microsoft Entra ID using client credentials."""
    tenant_id = creds["tenantId"]
    client_id = creds["clientId"]
    client_secret = creds["clientSecret"]

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )

    result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

    if "access_token" not in result:
        error = result.get("error_description", result.get("error", "Unknown error"))
        raise RuntimeError(f"Failed to authenticate with Microsoft Graph: {error}")

    logger.info("Successfully authenticated with Microsoft Graph API")
    return result["access_token"]


def get_site_id(access_token):
    """Get the SharePoint site ID from the site URL."""
    # Parse site URL: https://rccl.sharepoint.com/sites/CloudInfrastructureServices
    from urllib.parse import urlparse
    parsed = urlparse(SHAREPOINT_SITE_URL)
    hostname = parsed.hostname  # rccl.sharepoint.com
    site_path = parsed.path.rstrip("/")  # /sites/CloudInfrastructureServices

    url = f"{GRAPH_API_BASE}/sites/{hostname}:{site_path}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    site_id = response.json()["id"]
    logger.info(f"SharePoint site ID: {site_id}")
    return site_id


def get_default_drive_id(access_token, site_id):
    """Get the default document library (drive) for the site."""
    url = f"{GRAPH_API_BASE}/sites/{site_id}/drive"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    drive_id = response.json()["id"]
    logger.info(f"Default drive ID: {drive_id}")
    return drive_id


def sync_files(access_token, drive_id, site_id):
    """Recursively list and sync all supported files from the drive."""
    synced = 0
    skipped = 0
    failed = 0

    headers = {"Authorization": f"Bearer {access_token}"}

    # Use delta query if we have a previous delta link, otherwise list all
    url = f"{GRAPH_API_BASE}/sites/{site_id}/drive/root/children"

    # Recursively process folders
    stack = [("", url)]

    while stack:
        prefix, list_url = stack.pop()

        while list_url:
            response = requests.get(list_url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            for item in data.get("value", []):
                name = item.get("name", "")
                s3_key = f"sharepoint/{prefix}{name}" if prefix else f"sharepoint/{name}"

                if "folder" in item:
                    folder_path = f"{prefix}{name}".lower()
                    if any(folder_path.startswith(exc) for exc in EXCLUDED_FOLDERS):
                        logger.info(f"Skipping excluded folder: {prefix}{name}")
                        continue
                    # Queue folder for recursive processing
                    folder_url = f"{GRAPH_API_BASE}/sites/{site_id}/drive/items/{item['id']}/children"
                    stack.append((f"{prefix}{name}/", folder_url))
                    continue

                if "file" in item:
                    ext = os.path.splitext(name)[1].lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        logger.debug(f"Skipping unsupported file type: {name}")
                        skipped += 1
                        continue

                    # Check if file needs updating (compare lastModifiedDateTime)
                    if not needs_sync(s3_key, item):
                        logger.debug(f"Skipping unchanged file: {name}")
                        skipped += 1
                        continue

                    try:
                        download_and_upload(access_token, site_id, item, s3_key)
                        synced += 1
                    except Exception as e:
                        logger.error(f"Failed to sync {name}: {e}")
                        failed += 1

            # Handle pagination
            list_url = data.get("@odata.nextLink")

    return synced, skipped, failed


def needs_sync(s3_key, graph_item):
    """Check if the S3 object is older than the SharePoint file."""
    try:
        s3_head = s3.head_object(Bucket=BUCKET_NAME, Key=s3_key)
        s3_modified = s3_head["LastModified"]

        sp_modified_str = graph_item.get("lastModifiedDateTime", "")
        if sp_modified_str:
            sp_modified = datetime.fromisoformat(sp_modified_str.replace("Z", "+00:00"))
            if s3_modified >= sp_modified:
                return False
    except s3.exceptions.ClientError:
        pass  # File doesn't exist in S3 yet
    return True


def download_and_upload(access_token, site_id, item, s3_key):
    """Download a file from SharePoint and upload it to S3."""
    item_id = item["id"]
    name = item["name"]

    headers = {"Authorization": f"Bearer {access_token}"}
    download_url = f"{GRAPH_API_BASE}/sites/{site_id}/drive/items/{item_id}/content"

    logger.info(f"Syncing: {name} -> s3://{BUCKET_NAME}/{s3_key}")

    response = requests.get(download_url, headers=headers, stream=True, timeout=120)
    response.raise_for_status()

    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        tmp.flush()
        tmp.seek(0)

        s3.upload_fileobj(
            tmp,
            BUCKET_NAME,
            s3_key,
            ExtraArgs={
                "Metadata": {
                    "sharepoint-item-id": item_id,
                    "sharepoint-modified": item.get("lastModifiedDateTime", ""),
                    "sharepoint-author": item.get("lastModifiedBy", {}).get("user", {}).get("displayName", ""),
                },
            },
        )

