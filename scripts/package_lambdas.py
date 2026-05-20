"""Build and deploy Lambda packages for the RAG chatbot."""
import os
import subprocess
import sys
import tempfile
import zipfile
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def package_lambda(src_dir: str, output_zip: str, handler_file: str = None):
    """Package a Lambda function with its dependencies."""
    req_file = os.path.join(src_dir, "requirements.txt")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Install dependencies if requirements.txt exists
        if os.path.exists(req_file):
            print(f"  Installing dependencies from {req_file}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "-r", req_file,
                "-t", tmpdir,
                "--quiet",
                "--no-cache-dir",
            ])

        # Copy source files
        for f in os.listdir(src_dir):
            src_path = os.path.join(src_dir, f)
            if f.endswith(".py"):
                shutil.copy2(src_path, tmpdir)

        # Create zip
        print(f"  Creating {output_zip}...")
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, tmpdir)
                    zf.write(file_path, arcname)

    size_mb = os.path.getsize(output_zip) / (1024 * 1024)
    print(f"  Package size: {size_mb:.1f} MB")


def main():
    print("=== Packaging Bot Handler Lambda ===")
    package_lambda(
        src_dir=os.path.join(PROJECT_ROOT, "src", "bot"),
        output_zip=os.path.join(PROJECT_ROOT, "build", "bot-handler.zip"),
    )

    print("\n=== Packaging SharePoint Sync Lambda ===")
    package_lambda(
        src_dir=os.path.join(PROJECT_ROOT, "src", "sharepoint_sync"),
        output_zip=os.path.join(PROJECT_ROOT, "build", "sharepoint-sync.zip"),
    )

    print("\nDone! Deploy with:")
    print("  aws lambda update-function-code --function-name teams-rag-chatbot-dev-bot-handler \\")
    print("    --zip-file fileb://build/bot-handler.zip --profile shared --region us-east-1")
    print("  aws lambda update-function-code --function-name teams-rag-chatbot-dev-sharepoint-sync \\")
    print("    --zip-file fileb://build/sharepoint-sync.zip --profile shared --region us-east-1")


if __name__ == "__main__":
    os.makedirs(os.path.join(PROJECT_ROOT, "build"), exist_ok=True)
    main()
