# app/__init__.py
import sqlite3
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask
from flask_cors import CORS
from config import Config
import json
import os

# Global Firebase References (Agar bisa diimport file lain)
auth_db_ref = None
vault_db_ref = None

def init_sqlite():
    """Inisialisasi SQLite dengan Schema Lengkap (Termasuk TTL)"""
    try:
        with sqlite3.connect(Config.DB_FILE) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            
            # Tabel Session (Login & Interview)
            conn.execute('''CREATE TABLE IF NOT EXISTS sessions 
                         (token TEXT PRIMARY KEY, 
                          device_id TEXT, 
                          ip TEXT, 
                          status TEXT, 
                          type TEXT, 
                          created_at REAL, 
                          expires_at REAL)''')
            
            # Tabel Rate Limit
            conn.execute('''CREATE TABLE IF NOT EXISTS ratelimit 
                         (client_hash TEXT, hits INTEGER, window_start REAL)''')
            
            # Tabel Audit Log
            conn.execute('''CREATE TABLE IF NOT EXISTS audit_log
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp REAL, 
                          event TEXT, detail TEXT, anon_ip TEXT)''')
        print("✅ SQLite Initialized (WAL Mode)")
    except Exception as e:
        print(f"❌ SQLite Init Error: {e}")

def init_firebase():
    """Inisialisasi Dual Database Firebase"""
    global auth_db_ref, vault_db_ref
    
    # Cek apakah sudah ter-init sebelumnya (Mencegah error double init saat reload)
    if firebase_admin._apps:
        auth_app = firebase_admin.get_app('auth_app')
        vault_app = firebase_admin.get_app('vault_app')
        auth_db_ref = db.reference('/', app=auth_app)
        vault_db_ref = db.reference('/', app=vault_app)
        return

    try:
        # DB 1: Identity (Auth)
        c_auth = credentials.Certificate(json.loads(Config.AUTH_JSON))
        app_auth = firebase_admin.initialize_app(c_auth, {
            'databaseURL': Config.AUTH_DB_URL
        }, name='auth_app')
        auth_db_ref = db.reference('/', app=app_auth)

        # DB 2: Vault (Inbox)
        c_vault = credentials.Certificate(json.loads(Config.VAULT_JSON))
        app_vault = firebase_admin.initialize_app(c_vault, {
            'databaseURL': Config.VAULT_DB_URL
        }, name='vault_app')
        vault_db_ref = db.reference('/', app=app_vault)
        
        print("✅ Firebase Dual-Core Connected")
    except Exception as e:
        print(f"❌ Firebase Connection Failed: {e}")
        # Jangan raise error agar aplikasi tidak crash total, cukup log saja
        pass

def create_app():
    app = Flask(__name__)
    
    # Konfigurasi CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Inisialisasi Database
    init_sqlite()
    init_firebase()
    
    # Import Blueprints (Logic Modular)
    from app.routes_auth import bp_auth
    from app.routes_ai import bp_ai
    from app.routes_mail import bp_mail
    from app.routes_frontend import bp_frontend # <-- INI YANG BARU DITAMBAHKAN
    
    # Daftarkan Blueprints ke Aplikasi Utama
    app.register_blueprint(bp_auth, url_prefix='/api')
    app.register_blueprint(bp_ai, url_prefix='/api')
    app.register_blueprint(bp_mail, url_prefix='/api')
    
    # Frontend di root URL (Tanpa prefix /api)
    app.register_blueprint(bp_frontend)
    
    return app
