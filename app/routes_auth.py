# app/routes_auth.py
import time
import uuid
import hmac
import hashlib
import os
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import db_exec, db_query, hash_device, log_audit, rate_limit, get_anon_ip
from app import auth_db_ref # Import Global Firebase Ref
from config import Config

bp_auth = Blueprint('auth', __name__)

# --- ENDPOINT 1: CREATE ACCOUNT (WITH SIGNATURE) ---
@bp_auth.route('/create-account', methods=['POST'])
@rate_limit(limit=3, window=300) # Anti-Spam Registration
def create_account():
    data = request.json or {}
    
    # 1. Verifikasi Signature dari AI
    token = data.get('sess')
    dev_id = data.get('dev')
    sign_input = data.get('sign')
    
    expected_sign = hmac.new(Config.SECRET_KEY.encode(), f"{token}{dev_id}".encode(), hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(expected_sign, sign_input):
        log_audit("HACK", "Signature Tampering on Register", request)
        return jsonify({"error": "Security Violation"}), 403

    # 2. Cek Username Unik (DB Auth)
    username = data.get('username')
    if not username or len(username) < 3:
        return jsonify({"error": "Invalid Username"}), 400
        
    if auth_db_ref.child(f'users/{username}').get():
        return jsonify({"error": "Username taken"}), 400

    # 3. Generate Mailbox ID (The Secret Link)
    mailbox_id = str(uuid.uuid4())

    # 4. Simpan Identity
    user_payload = {
        "username": username,
        "alias": f"{data.get('alias')}@defacer.dedyn.io",
        "password_hash": generate_password_hash(data.get('password')),
        "device_bound": hash_device(dev_id), # Bind ke Hash Device
        "mailbox_id": mailbox_id,
        "created_at": {".sv": "timestamp"},
        "settings": {"forward_url": ""}
    }
    
    auth_db_ref.child(f'users/{username}').set(user_payload)
    
    # Hapus sesi interview (bersih-bersih)
    db_exec("DELETE FROM sessions WHERE token=?", (token,))
    
    return jsonify({"status": "CREATED"})

# --- ENDPOINT 2: LOGIN (SESSION GENERATOR) ---
@bp_auth.route('/login', methods=['POST'])
@rate_limit(limit=5, window=60) # Anti Brute Force
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    dev_id_input = data.get('device_id')

    # 1. Ambil User dari Firebase
    user_ref = auth_db_ref.child(f'users/{username}').get()
    
    # 2. Validasi Password (Timing Attack Safe)
    if not user_ref or not check_password_hash(user_ref.get('password_hash', ''), password):
        time.sleep(1) # Fake delay
        return jsonify({"error": "Invalid Credentials"}), 401

    # 3. Validasi Device Binding (Mencegah Login di HP Lain)
    if user_ref.get('device_bound') != hash_device(dev_id_input):
        log_audit("BLOCK", f"Device Mismatch: {username}", request)
        return jsonify({"error": "Device Not Recognized"}), 403

    # 4. Buat Token Login (24 Jam)
    entropy = f"LOGIN{username}{time.time()}{os.urandom(8)}"
    session_token = hmac.new(Config.SECRET_KEY.encode(), entropy.encode(), hashlib.sha256).hexdigest()
    
    now = time.time()
    expires_at = now + Config.SESSION_TTL_LOGIN
    
    # Simpan Session (Type: LOGIN)
    db_exec("INSERT INTO sessions (token, device_id, ip, status, type, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?)", 
            (session_token, dev_id_input, get_anon_ip(request), "LOGGED_IN", "LOGIN", now, expires_at))

    return jsonify({"status": "SUCCESS", "token": session_token, "alias": user_ref.get('alias')})
