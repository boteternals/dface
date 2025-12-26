import os
import json
import sys

class Config:
    # 1. BASIC SECURITY
    SECRET_KEY = os.environ.get("SECRET_KEY")
    ENCRYPTION_KEY = os.environ.get("DATA_ENCRYPTION_KEY")
    
    # 2. FIREBASE CONFIG (ENV JSON & URL)
    AUTH_JSON = os.environ.get("FIREBASE_AUTH_JSON")
    VAULT_JSON = os.environ.get("FIREBASE_VAULT_JSON")
    AUTH_DB_URL = os.environ.get("FIREBASE_AUTH_URL")
    VAULT_DB_URL = os.environ.get("FIREBASE_VAULT_URL")

    # 3. SESSION RULES (FIXING TTL BUG)
    # Session login mati dalam 24 jam. Interview mati dalam 15 menit.
    SESSION_TTL_LOGIN = 86400  # 24 Jam
    SESSION_TTL_INTERVIEW = 900 # 15 Menit

    # 4. DATABASE FILE
    DB_FILE = "dguard.db"

    @staticmethod
    def check_health():
        required = [
            "SECRET_KEY", "DATA_ENCRYPTION_KEY", 
            "FIREBASE_AUTH_JSON", "FIREBASE_VAULT_JSON",
            "FIREBASE_AUTH_URL", "FIREBASE_VAULT_URL"
        ]
        missing = [v for v in required if not os.environ.get(v)]
        if missing:
            print(f"FATAL: Missing ENV Variables: {', '.join(missing)}")
            sys.exit(1)

# Auto check saat import
Config.check_health()
