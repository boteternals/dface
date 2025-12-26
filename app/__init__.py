import sqlite3
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask
from flask_cors import CORS
from config import Config
import json

# Global Firebase References
auth_db_ref = None
vault_db_ref = None

def init_sqlite():
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        
        # [FIX 3 & 4] Tambah kolom 'expires_at' dan 'type'
        conn.execute('''CREATE TABLE IF NOT EXISTS sessions 
                     (token TEXT PRIMARY KEY, 
                      device_id TEXT, 
                      ip TEXT, 
                      status TEXT, 
                      type TEXT, 
                      created_at REAL, 
                      expires_at REAL)''')
        
        # Rate Limit Table
        conn.execute('''CREATE TABLE IF NOT EXISTS ratelimit 
                     (client_hash TEXT, hits INTEGER, window_start REAL)''')
        
        # Audit Log
        conn.execute('''CREATE TABLE IF NOT EXISTS audit_log
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, 
                      event TEXT, detail TEXT, anon_ip TEXT)''')
    print("WAL Mode")

def init_firebase():
    """Dual Database Init"""
    global auth_db_ref, vault_db_ref
    try:
        # DB 1: Identity
        c_auth = credentials.Certificate(json.loads(Config.AUTH_JSON))
        app_auth = firebase_admin.initialize_app(c_auth, {
            'databaseURL': Config.AUTH_DB_URL
        }, name='auth_app')
        auth_db_ref = db.reference('/', app=app_auth)

        # DB 2: Vault
        c_vault = credentials.Certificate(json.loads(Config.VAULT_JSON))
        app_vault = firebase_admin.initialize_app(c_vault, {
            'databaseURL': Config.VAULT_DB_URL
        }, name='vault_app')
        vault_db_ref = db.reference('/', app=app_vault)
        
        print("Database Connected")
    except Exception as e:
        print(f"Error: {e}")
        raise e

def create_app():
    app = Flask(__name__)
    
    # [FIX 8] Strict CORS (Bisa diperketat lagi nanti jika punya domain frontend fix)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Init DBs
    init_sqlite()
    init_firebase()
    
    # Register Blueprints (Kita buat di respon berikutnya)
    from app.routes_auth import bp_auth
    from app.routes_ai import bp_ai
    from app.routes_mail import bp_mail
    
    app.register_blueprint(bp_auth, url_prefix='/api')
    app.register_blueprint(bp_ai, url_prefix='/api')
    app.register_blueprint(bp_mail, url_prefix='/api')
    
    return app
