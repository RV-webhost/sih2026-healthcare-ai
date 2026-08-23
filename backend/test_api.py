import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Explicitly load .env file from project root or backend folder
env_path = project_root / ".env"
if not env_path.exists():
    env_path = backend_dir / ".env"

load_dotenv(dotenv_path=env_path, override=True)

print(f"[INFO] Loaded .env from: {env_path}")
print(f"[INFO] Database URI: {os.getenv('DATABASE_URL')}")

from app import create_app

app = create_app()

with app.test_client() as client:
    print("\n--- Making GET request to /api/v1/doctors ---")
    response = client.get("/api/v1/doctors")
    print(f"Status Code: {response.status_code}\n")
    print("Response JSON Output:")
    try:
        json_output = response.get_json()
        print(json.dumps(json_output, indent=2))
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("Raw Data:", response.data.decode("utf-8"))
