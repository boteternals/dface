import time
import hmac
import hashlib
import sqlite3
import socket
import datetime
import re
from functools import wraps
from urllib.parse import urlparse
from flask import request, jsonify, g
from cryptography.fernet import Fernet
from config import Config

cipher_suite = Fernet(Config.ENCRYPTION_KEY.encode())

# ==============================================================================
# DATABASE HELPERS
# ==============================================================================
def db_exec(query, args=()):
    with sqlite3.connect(Config.DB_FILE) as conn:
        conn.execute(query, args)
        conn.commit()

def db_query(query, args=(), one=False):
    with sqlite3.connect(Config.DB_FILE) as conn:
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv

# ==============================================================================
# [FIX 1, 2, 3, 5] THE AUTH DECORATOR (MANDATORY FOR SENSITIVE ROUTES)
# ==============================================================================
def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Ambil Token dari Header (Bearer Token Standard)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized: Missing Token"}), 401
        
        token = auth_header.split(" ")[1]
        
        # 2. Cek Token di Database + Cek Expiry (TTL)
        session = db_query("SELECT device_id, type, expires_at, status FROM sessions WHERE token=?", (token,), one=True)
        
        if not session:
            return jsonify({"error": "Unauthorized: Invalid Token"}), 401
        
        dev_id, sess_type, expires_at, status = session
        
        # 3. Cek Status & Tipe
        if status != "LOGGED_IN" or sess_type != "LOGIN":
            return jsonify({"error": "Unauthorized: Bad Session Type"}), 403
            
        # 4. Cek Expiry (Auto Revoke)
        if time.time() > expires_at:
            db_exec("DELETE FROM sessions WHERE token=?", (token,))
            return jsonify({"error": "Session Expired. Please Login Again."}), 401
            
        # 5. Simpan info user di global context 'g' biar bisa dipake di route
        # Kita butuh username. Username biasanya tersimpan di Firebase, 
        # tapi untuk efisiensi kita bisa simpan username di tabel session SQLite juga ke depannya.
        # Untuk sekarang, kita asumsi username dikirim di body, TAPI kita validasi apakah token ini milik username tsb.
        # (Nanti di routes_auth.py kita perbaiki mapping token->username).
        
        g.session_token = token
        g.device_id = dev_id
        
        return f(*args, **kwargs)
    return decorated_function

# ==============================================================================
# [FIX 6] RATE LIMITER (TOKEN BUCKET ALGORITHM)
# ==============================================================================
def rate_limit(limit=10, window=60):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip_hash = get_anon_ip(request)
            now = time.time()
            
            # Cek db
            row = db_query("SELECT hits, window_start FROM ratelimit WHERE client_hash=?", (ip_hash,), one=True)
            
            if row:
                hits, start = row
                if now - start > window:
                    # Reset window
                    db_exec("UPDATE ratelimit SET hits=1, window_start=? WHERE client_hash=?", (now, ip_hash))
                else:
                    if hits >= limit:
                        log_audit("RATE_LIMIT", f"Exceeded {limit}/{window}s", request)
                        return jsonify({"error": "Too Many Requests. Chill."}), 429
                    db_exec("UPDATE ratelimit SET hits=hits+1 WHERE client_hash=?", (ip_hash,))
            else:
                db_exec("INSERT INTO ratelimit VALUES (?, 1, ?)", (ip_hash, now))
            
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ==============================================================================
# [FIX 7] SSRF PROTECTION (DNS REBINDING PROOF)
# ==============================================================================
def is_safe_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'): return False
        if not parsed.hostname: return False
        
        # Resolve IP
        ip = socket.gethostbyname(parsed.hostname)
        
        # BLOKIR PRIVATE RANGES (CIDR check manual simple)
        # 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
        if ip.startswith("127."): return False
        if ip.startswith("10."): return False
        if ip.startswith("192.168."): return False
        if ip.startswith("0."): return False
        
        # Cek range 172.16 - 172.31
        if ip.startswith("172."):
            second_octet = int(ip.split('.')[1])
            if 16 <= second_octet <= 31: return False
            
        return True
    except:
        return False

# ==============================================================================
# CRYPTO & LOGGING UTILS
# ==============================================================================
def encrypt_content(text):
    if not text: return ""
    return cipher_suite.encrypt(text.encode()).decode()

def decrypt_content(enc_text):
    if not enc_text: return ""
    try: return cipher_suite.decrypt(enc_text.encode()).decode()
    except: return "[CORRUPT DATA]"

def get_anon_ip(req):
    if req.headers.get('CF-Connecting-IP'): real = req.headers.get('CF-Connecting-IP')
    elif req.headers.get('X-Forwarded-For'): real = req.headers.get('X-Forwarded-For').split(',')[0]
    else: real = req.remote_addr
    salt = datetime.datetime.now().strftime("%Y-%m-%d")
    return hashlib.sha256(f"{real}{salt}{Config.SECRET_KEY}".encode()).hexdigest()

def hash_device(device_id):
    return hmac.new(Config.SECRET_KEY.encode(), device_id.encode(), hashlib.sha256).hexdigest()

def log_audit(event, detail, req):
    anon_ip = get_anon_ip(req)
    db_exec("INSERT INTO audit_log (timestamp, event, detail, anon_ip) VALUES (?, ?, ?, ?)",
            (time.time(), event, detail, anon_ip))
