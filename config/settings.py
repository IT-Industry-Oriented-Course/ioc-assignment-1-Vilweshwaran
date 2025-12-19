"""Configuration settings for the Clinical Workflow Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"


LOGS_DIR.mkdir(exist_ok=True)


HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")


DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", LOGS_DIR / "audit.jsonl"))


AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
