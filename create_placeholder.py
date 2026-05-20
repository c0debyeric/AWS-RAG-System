import zipfile
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
zip_path = os.path.join(script_dir, "terraform", "modules", "bot-service", "placeholder.zip")

with zipfile.ZipFile(zip_path, "w") as z:
    z.writestr("app.py", 'def handler(event, context): return {"statusCode": 200, "body": "placeholder"}')

print(f"Created {zip_path}")
