from pathlib import Path


APP_VERSION = "0.1.0"
GITHUB_OWNER = "OWNER"
GITHUB_REPO = "REPO"
ASSET_NAME = "BinderSetup.exe"

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "events.jsonl"
APP_LOG_FILE = LOG_DIR / "app.log"
PROFILES_FILE = DATA_DIR / "profiles.json"
