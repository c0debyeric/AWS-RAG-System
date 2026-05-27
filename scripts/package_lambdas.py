"""Build Lambda deployment packages for the RAG chatbot.

Each Lambda zip includes:
  - The handler file
  - Shared src/ modules (common, ingestion, retrieval, conversation_logging)
  - pip dependencies
"""
import os
import subprocess
import sys
import tempfile
import zipfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

# Shared modules that get bundled into Lambda zips
SHARED_MODULES = ["common", "ingestion", "retrieval", "conversation_logging"]

# Dependencies for each Lambda
BOT_REQUIREMENTS = [
    "boto3>=1.34",
    "psycopg2-binary>=2.9",
    "pgvector>=0.3",
    "tiktoken>=0.7",
    "numpy>=1.26",
    "pdfplumber>=0.11",
    "python-docx>=1.1",
    "beautifulsoup4>=4.12",
]

SETUP_REQUIREMENTS = [
    "psycopg2-binary>=2.9",
]

SYNC_REQUIREMENTS = [
    "boto3>=1.34",
    "msal>=1.28",
    "requests>=2.31",
]


def copy_shared_modules(dest_dir: str):
    """Copy shared src/ modules into the Lambda package directory."""
    for module in SHARED_MODULES:
        src_path = os.path.join(SRC_DIR, module)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, os.path.join(dest_dir, module))


def install_requirements(requirements: list[str], dest_dir: str):
    """Install pip packages into dest_dir."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as req_file:
        req_file.write("\n".join(requirements))
        req_file.flush()
        req_path = req_file.name

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", req_path,
            "-t", dest_dir,
            "--quiet",
            "--no-cache-dir",
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


def main():
    package_pgvector_setup_handler()
    package_bot_handler()
    package_ingest_handler()
    package_sharepoint_sync()

    print("\n=== Done! Deploy with: ===")
    print("  aws lambda update-function-code --function-name <project>-<environment>-pgvector-setup \\")
    print("    --zip-file fileb://build/pgvector-setup.zip --profile shared --region us-east-1")
    print("  aws lambda update-function-code --function-name rag-bot-handler \\")
    print("    --zip-file fileb://build/bot-handler.zip --profile shared --region us-east-1")
    print("  aws lambda update-function-code --function-name rag-ingest-handler \\")
    print("    --zip-file fileb://build/ingest-handler.zip --profile shared --region us-east-1")
    print("  aws lambda update-function-code --function-name rag-sharepoint-sync \\")
    print("    --zip-file fileb://build/sharepoint-sync.zip --profile shared --region us-east-1")


if __name__ == "__main__":
    os.makedirs(os.path.join(PROJECT_ROOT, "build"), exist_ok=True)
    main()
