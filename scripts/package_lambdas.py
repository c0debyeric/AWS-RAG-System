"""Build and optionally deploy Lambda deployment packages for the RAG chatbot.

Each Lambda zip includes:
  - The handler file
  - Shared src/ modules (common, ingestion, retrieval, conversation_logging)
  - Dependencies (installed via uv)

Usage:
  python scripts/package_lambdas.py           # package only
  python scripts/package_lambdas.py --deploy   # package + deploy all
"""
import argparse
import os
import subprocess
import tempfile
import zipfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

# Shared modules that get bundled into Lambda zips
SHARED_MODULES = ["common", "ingestion", "retrieval", "conversation_logging"]

# Dependencies for each Lambda (pinned to latest stable)
BOT_REQUIREMENTS = [
    "boto3>=1.36,<2",
    "psycopg2-binary>=2.9.10,<3",
    "pgvector>=0.3.6,<1",
    "tiktoken>=0.8,<1",
    "numpy>=2.0,<3",
    "pdfplumber>=0.11.4,<1",
    "python-docx>=1.1.2,<2",
    "beautifulsoup4>=4.12.3,<5",
]

SETUP_REQUIREMENTS = [
    "psycopg2-binary>=2.9.10,<3",
]

SYNC_REQUIREMENTS = [
    "boto3>=1.36,<2",
    "msal>=1.31,<2",
    "requests>=2.32,<3",
]


def copy_shared_modules(dest_dir: str):
    """Copy shared src/ modules into the Lambda package directory."""
    for module in SHARED_MODULES:
        src_path = os.path.join(SRC_DIR, module)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, os.path.join(dest_dir, module))


def install_requirements(requirements: list[str], dest_dir: str):
    """Install packages into dest_dir using uv."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as req_file:
        req_file.write("\n".join(requirements))
        req_file.flush()
        req_path = req_file.name

    try:
        subprocess.check_call([
            "uv", "pip", "install",
            "-r", req_path,
            "--target", dest_dir,
            "--quiet",
            "--no-build",
            "--python-platform", "manylinux2014_x86_64",
            "--python-version", "3.13",
        ])
    finally:
        os.unlink(req_path)


def create_zip(source_dir: str, output_zip: str):
    """Create a zip file from a directory."""
    os.makedirs(os.path.dirname(output_zip), exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                file_path = os.path.join(root, f)
                arcname = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arcname)

    size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"  Package size: {size_mb:.1f} MB")


def package_bot_handler():
    """Package the bot handler Lambda (query pipeline)."""
    print("=== Packaging Bot Handler Lambda ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy handler
        shutil.copy2(os.path.join(SRC_DIR, "bot", "app.py"), tmpdir)

        # Copy shared modules
        copy_shared_modules(tmpdir)

        # Install deps
        print("  Installing dependencies...")
        install_requirements(BOT_REQUIREMENTS, tmpdir)

        # Create zip
        output = os.path.join(PROJECT_ROOT, "build", "bot-handler.zip")
        create_zip(tmpdir, output)
        print(f"  Created {output}")


def package_pgvector_setup_handler():
    """Package the one-time pgvector setup Lambda."""
    print("\n=== Packaging Pgvector Setup Lambda ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copy2(os.path.join(PROJECT_ROOT, "lambdas", "setup_handler.py"), tmpdir)
        shutil.copy2(os.path.join(PROJECT_ROOT, "scripts", "setup_pgvector.py"), tmpdir)

        print("  Installing dependencies...")
        install_requirements(SETUP_REQUIREMENTS, tmpdir)

        output = os.path.join(PROJECT_ROOT, "build", "pgvector-setup.zip")
        create_zip(tmpdir, output)
        print(f"  Created {output}")


def package_ingest_handler():
    """Package the ingestion Lambda (S3 event triggered)."""
    print("\n=== Packaging Ingest Handler Lambda ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy handler
        handler_src = os.path.join(PROJECT_ROOT, "lambdas", "ingest_handler.py")
        shutil.copy2(handler_src, tmpdir)

        # Copy shared modules
        copy_shared_modules(tmpdir)

        # Install deps (same as bot — needs parsers + embedder)
        print("  Installing dependencies...")
        install_requirements(BOT_REQUIREMENTS, tmpdir)

        output = os.path.join(PROJECT_ROOT, "build", "ingest-handler.zip")
        create_zip(tmpdir, output)
        print(f"  Created {output}")


def package_sharepoint_sync():
    """Package the SharePoint sync Lambda."""
    print("\n=== Packaging SharePoint Sync Lambda ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy handler
        for f in os.listdir(os.path.join(SRC_DIR, "sharepoint_sync")):
            if f.endswith(".py"):
                shutil.copy2(os.path.join(SRC_DIR, "sharepoint_sync", f), tmpdir)

        # Install deps
        print("  Installing dependencies...")
        install_requirements(SYNC_REQUIREMENTS, tmpdir)

        output = os.path.join(PROJECT_ROOT, "build", "sharepoint-sync.zip")
        create_zip(tmpdir, output)
        print(f"  Created {output}")


AWS_PROFILE = "shared"
AWS_REGION = "us-east-1"
S3_BUCKET = "teams-rag-chatbot-dev-documents-044061434394"
S3_PREFIX = "lambda-artifacts"

# 50 MB — Lambda direct upload limit
DIRECT_UPLOAD_LIMIT = 50 * 1024 * 1024

# Map zip filenames → Lambda function names
FUNCTION_MAP = {
    "pgvector-setup.zip": "teams-rag-chatbot-dev-pgvector-setup",
    "bot-handler.zip": "teams-rag-chatbot-dev-query-handler",
    "ingest-handler.zip": "teams-rag-chatbot-dev-ingest-handler",
    "sharepoint-sync.zip": "teams-rag-chatbot-dev-sharepoint-sync",
}


def deploy_lambda(zip_path: str, function_name: str):
    """Deploy a Lambda zip — direct upload if < 50 MB, otherwise via S3."""
    zip_name = os.path.basename(zip_path)
    size = os.path.getsize(zip_path)

    if size < DIRECT_UPLOAD_LIMIT:
        print(f"  Deploying {zip_name} → {function_name} (direct upload)...")
        subprocess.check_call([
            "aws", "lambda", "update-function-code",
            "--function-name", function_name,
            "--zip-file", f"fileb://{zip_path}",
            "--profile", AWS_PROFILE,
            "--region", AWS_REGION,
            "--output", "text",
            "--query", "CodeSize",
        ])
    else:
        s3_key = f"{S3_PREFIX}/{zip_name}"
        print(f"  Uploading {zip_name} → s3://{S3_BUCKET}/{s3_key}...")
        subprocess.check_call([
            "aws", "s3", "cp", zip_path,
            f"s3://{S3_BUCKET}/{s3_key}",
            "--profile", AWS_PROFILE,
            "--region", AWS_REGION,
        ])
        print(f"  Deploying {zip_name} → {function_name} (via S3)...")
        subprocess.check_call([
            "aws", "lambda", "update-function-code",
            "--function-name", function_name,
            "--s3-bucket", S3_BUCKET,
            "--s3-key", s3_key,
            "--profile", AWS_PROFILE,
            "--region", AWS_REGION,
            "--output", "text",
            "--query", "CodeSize",
        ])

    print(f"  ✓ {function_name} deployed")


def main():
    parser = argparse.ArgumentParser(description="Package and deploy Lambda functions")
    parser.add_argument("--deploy", action="store_true", help="Deploy to AWS after packaging")
    args = parser.parse_args()

    os.makedirs(os.path.join(PROJECT_ROOT, "build"), exist_ok=True)

    package_pgvector_setup_handler()
    package_bot_handler()
    package_ingest_handler()
    package_sharepoint_sync()

    if args.deploy:
        print("\n=== Deploying to AWS ===")
        for zip_name, function_name in FUNCTION_MAP.items():
            zip_path = os.path.join(PROJECT_ROOT, "build", zip_name)
            deploy_lambda(zip_path, function_name)
        print("\n=== All functions deployed! ===")
    else:
        print("\n=== Done! Run with --deploy to push to AWS ===")


if __name__ == "__main__":
    main()
