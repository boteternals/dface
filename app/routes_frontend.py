# app/routes_frontend.py
from flask import Blueprint, send_from_directory
import os

# Definisikan Blueprint untuk Frontend
bp_frontend = Blueprint('frontend', __name__)

@bp_frontend.route('/')
def index():
    # Saat user membuka domain utama, kirim index.html
    # Flask otomatis mencari di folder 'app/static' karena struktur package kita
    return send_from_directory('static', 'index.html')

@bp_frontend.route('/<path:path>')
def static_files(path):
    # Menangani permintaan file CSS, JS, Gambar, dll
    return send_from_directory('static', path)
