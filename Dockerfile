# Gunakan Python 3.11 versi Slim (Ringan & Cepat)
FROM python:3.11-slim

# Set Environment Variables agar log Python muncul realtime di Zeabur
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Buat folder kerja di dalam container
WORKDIR /app

# 1. Copy requirements dulu (agar Docker bisa cache layer ini)
COPY requirements.txt .

# 2. Install Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy seluruh sisa kode sumber (run.py, config.py, app folder)
COPY . .

# Expose Port 8080 (Standar Zeabur/Cloud)
EXPOSE 8080

# Perintah Eksekusi Server (Menggunakan Gunicorn via run.py)
# Workers 4 = Bisa handle 4 request paralel
# Timeout 120 = Biar AI gak putus koneksi kalau mikirnya lama
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120"]
