# app/routes_mail.py
# ARCHITECT: ETERNALS DEV
# MODULE: MAIL LOGIC (INBOX, SETTINGS, BRIDGE)

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, request, jsonify, g
from app.utils import require_auth, is_safe_url, encrypt_content, decrypt_content, hash_device, log_audit, rate_limit
from app import auth_db_ref, vault_db_ref # Import Global DB Refs

bp_mail = Blueprint('mail', __name__)

# ==============================================================================
# HELPER: OWNERSHIP CHECK
# ==============================================================================
def verify_ownership(username):
    """
    Memastikan User A hanya bisa akses data User A.
    Menggunakan Device ID dari Token Login sebagai bukti kepemilikan.
    """
    # Ambil user dari Firebase Identity DB
    user_ref = auth_db_ref.child(f'users/{username}').get()
    if not user_ref:
        return None
    
    # Bandingkan Device Hash di DB dengan Device Hash dari Token Login
    # (g.device_id diisi otomatis oleh decorator @require_auth)
    stored_dev_hash = user_ref.get('device_bound')
    current_dev_hash = hash_device(g.device_id)
    
    if stored_dev_hash != current_dev_hash:
        return None # Mismatch / Hack attempt
        
    return user_ref # Return data user jika valid

# ==============================================================================
# ENDPOINT 1: USER SETTINGS (SECURED)
# ==============================================================================
@bp_mail.route('/settings', methods=['POST'])
@require_auth # Wajib Login
def update_settings():
    data = request.json or {}
    username = data.get('username')
    webhook_url = data.get('webhook_url', '').strip()
    
    # 1. Validasi Ownership
    # Mencegah Attacker mengubah webhook orang lain
    if not verify_ownership(username):
        log_audit("HACK", f"Unauthorized Settings Access: {username}", request)
        return jsonify({"error": "Access Denied"}), 403
    
    # 2. SSRF Protection (Cek Utils)
    if webhook_url and not is_safe_url(webhook_url):
        log_audit("SSRF", "Malicious Webhook Blocked", request)
        return jsonify({"error": "Unsafe URL Detected"}), 400

    # 3. Update Firebase
    auth_db_ref.child(f'users/{username}/settings').update({"forward_url": webhook_url})
    return jsonify({"status": "UPDATED"})

# ==============================================================================
# ENDPOINT 2: FETCH INBOX (SECURED)
# ==============================================================================
@bp_mail.route('/inbox', methods=['POST'])
@require_auth # Wajib Login
def get_inbox():
    data = request.json or {}
    username = data.get('username')
    
    # 1. Validasi Ownership
    # Mencegah Attacker membaca inbox orang lain
    user_ref = verify_ownership(username)
    if not user_ref:
        return jsonify({"error": "Access Denied"}), 403
    
    mailbox_id = user_ref.get('mailbox_id')
    
    # 2. Ambil Email dari Vault (Limit 5 Terakhir)
    raw_inbox = vault_db_ref.child(f'inboxes/{mailbox_id}').order_by_key().limit_to_last(5).get()
    
    clean_inbox = []
    if raw_inbox:
        for k, v in raw_inbox.items():
            # Dekripsi Konten untuk ditampilkan ke User
            clean_inbox.append({
                "id": k,
                "from": v.get('from'),
                "subject": decrypt_content(v.get('subject')),
                "body": decrypt_content(v.get('body')),
                "time": v.get('timestamp')
            })
            
    # Urutkan dari yang terbaru
    clean_inbox.reverse()
    return jsonify(clean_inbox)

# ==============================================================================
# ENDPOINT 3: INBOUND WEBHOOK (UNIVERSAL PARSER)
# ==============================================================================
# Endpoint ini PUBLIK karena dipanggil oleh ForwardEmail / Cloudflare
@bp_mail.route('/webhook-inbound', methods=['POST'])
def inbound_mail():
    # Support berbagai format (JSON / Form Data)
    data = request.json or request.form
    
    # Debugging: Print payload masuk ke log Zeabur (Cek tab Logs jika email ga masuk)
    print(f"DEBUG INBOUND PAYLOAD: {data}", flush=True)

    # 1. Normalisasi Data (Parsing Cerdas)
    # ForwardEmail kadang pakai 'sender', Cloudflare pakai 'from'
    sender = data.get('from') or data.get('sender') or 'Unknown Sender'
    recipient = data.get('to') or data.get('recipient') or ''
    subject = data.get('subject') or '(No Subject)'
    
    # Ambil body (Text priority, fallback ke HTML)
    body = data.get('text') or data.get('html') or ''

    # 2. Parsing Username dari Recipient
    # Contoh: "admin@defacer.dedyn.io" -> ambil "admin"
    try: 
        # Handle format ribet: "Nama User <admin@domain.com>"
        if '<' in recipient: 
            raw_email = recipient.split('<')[1].split('>')[0]
            username = raw_email.split('@')[0]
        else:
            username = recipient.split('@')[0]
    except: 
        print(f"DEBUG: Bad Recipient Format: {recipient}")
        return jsonify({"status": "IGNORED", "reason": "Bad Recipient Format"}), 200

    # 3. Cek User Exist (DB Auth)
    # Kita hanya terima email untuk user yang terdaftar di sistem kita
    user_ref = auth_db_ref.child(f'users/{username}').get()
    if not user_ref: 
        print(f"DEBUG: Rejected. User '{username}' not found.")
        return jsonify({"status": "REJECTED"}), 200

    mailbox_id = user_ref.get('mailbox_id')
    
    # 4. Enkripsi Konten (Zeabur Encrypts -> Firebase Stores)
    enc_sub = encrypt_content(subject)
    enc_body = encrypt_content(body)

    # 5. Simpan ke Vault (Secure Storage)
    vault_ref = vault_db_ref.child(f'inboxes/{mailbox_id}')
    vault_ref.push({
        "from": sender,
        "subject": enc_sub,
        "body": enc_body,
        "timestamp": {".sv": "timestamp"}
    })

    # 6. Auto Purge (Jaga Inbox tetap Ephemeral > 5 Email)
    msgs = vault_ref.order_by_key().get()
    if msgs and len(msgs) > 5:
        sorted_keys = sorted(msgs.keys())
        # Hitung berapa yang harus dihapus
        excess = len(msgs) - 5
        for k in sorted_keys[:excess]:
            vault_ref.child(k).delete()

    # 7. Forwarding (User Webhook)
    # Jika user punya setting webhook sendiri, kita lempar datanya (tetap terenkripsi)
    user_settings = user_ref.get('settings', {})
    fwd_url = user_settings.get('forward_url')
    
    if fwd_url:
        try:
            requests.post(fwd_url, json={
                "event": "INCOMING_MAIL",
                "to": recipient,
                "from": sender,
                "subject_enc": enc_sub, # Tetap kirim terenkripsi demi keamanan
                "body_enc": enc_body,
                "note": "Content encrypted. Use your Fernet Key to decrypt."
            }, timeout=3)
        except Exception as e:
            print(f"DEBUG: Webhook Forward Failed: {e}")

    return jsonify({"status": "RECEIVED"}), 200

# ==============================================================================
# ENDPOINT 4: SMTP BRIDGE (SECURED)
# ==============================================================================
@bp_mail.route('/send-bridge', methods=['POST'])
@require_auth # Wajib Login
@rate_limit(limit=3, window=60) # Rate Limit Ketat (Anti Spam)
def send_bridge():
    data = request.json or {}
    
    # Validasi Input Basic
    required_fields = ['smtp_host', 'smtp_user', 'smtp_pass', 'to', 'message']
    if not all(k in data for k in required_fields):
        return jsonify({"error": "Missing SMTP Credentials or Data"}), 400

    try:
        # Susun Email
        msg = MIMEMultipart()
        msg['From'] = data.get('smtp_user')
        msg['To'] = data.get('to')
        msg['Subject'] = data.get('subject', '(No Subject)')
        msg.attach(MIMEText(data.get('message'), 'plain'))

        # Kirim pakai Server SMTP User Sendiri
        # Port default 587 (TLS), fallback manual jika perlu
        port = int(data.get('smtp_port', 587))
        
        server = smtplib.SMTP(data.get('smtp_host'), port)
        server.starttls()
        server.login(data.get('smtp_user'), data.get('smtp_pass'))
        server.sendmail(data.get('smtp_user'), data.get('to'), msg.as_string())
        server.quit()
        
        log_audit("OUTBOUND", f"Bridge Used: {data.get('smtp_host')}", request)
        return jsonify({"status": "SENT"})
    except Exception as e:
        return jsonify({"error": f"SMTP Error: {str(e)}"}), 500
