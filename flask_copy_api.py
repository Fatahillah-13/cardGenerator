from flask import Flask, jsonify
import os
import shutil
from datetime import datetime

app = Flask(__name__)

# === KONFIGURASI ===
SOURCE_FOLDER = r"D:\sistem_cetak_idcard\pics\public\storage"
DEST_FOLDER = r"C:\coba_pindah"

def format_time(epoch_time):
    return datetime.fromtimestamp(epoch_time).strftime("%Y-%m-%d %H:%M:%S")

@app.route('/copy-files', methods=['POST'])
def copy_files():
    os.makedirs(DEST_FOLDER, exist_ok=True)
    log_file = os.path.join(SOURCE_FOLDER, f"log_copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    copied_files = []
    skipped_files = []

    for filename in os.listdir(SOURCE_FOLDER):
        if not (filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg")):
            continue

        src = os.path.join(SOURCE_FOLDER, filename)
        dst = os.path.join(DEST_FOLDER, filename)

        if os.path.isfile(src):
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                src_mtime = os.path.getmtime(src)
                copied_files.append((filename, "Baru", format_time(src_mtime), "-"))
            else:
                src_mtime = os.path.getmtime(src)
                dst_mtime = os.path.getmtime(dst)
                if src_mtime > dst_mtime:
                    shutil.copy2(src, dst)
                    copied_files.append((filename, "Lebih baru", format_time(src_mtime), format_time(dst_mtime)))
                else:
                    skipped_files.append((filename, format_time(src_mtime), format_time(dst_mtime)))

    # Buat log file
    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"LOG PROSES PENYALINAN FILE JPG/JPEG\n")
        log.write(f"Tanggal proses: {datetime.now()}\n")
        log.write(f"Sumber: {SOURCE_FOLDER}\n")
        log.write(f"Tujuan: {DEST_FOLDER}\n")
        log.write("="*80 + "\n\n")

        log.write(f"FILE YANG DISALIN ({len(copied_files)}):\n")
        for f, status, src_time, dst_time in copied_files:
            log.write(f"  - {f} ({status})\n")
            log.write(f"    Waktu sumber: {src_time}\n")
            if dst_time != "-":
                log.write(f"    Waktu lama di tujuan: {dst_time}\n")
            log.write("\n")

        log.write(f"FILE YANG DILEWATI ({len(skipped_files)}):\n")
        for f, src_time, dst_time in skipped_files:
            log.write(f"  - {f}\n")
            log.write(f"    Waktu sumber: {src_time}\n")
            log.write(f"    Waktu tujuan: {dst_time}\n\n")

        log.write("="*80 + "\n")
        log.write(f"Total file disalin  : {len(copied_files)}\n")
        log.write(f"Total file dilewati : {len(skipped_files)}\n")

    return jsonify({
        "status": "success",
        "copied": len(copied_files),
        "skipped": len(skipped_files),
        "log_file": log_file
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
