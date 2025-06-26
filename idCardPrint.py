from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import os
import logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# === Font Config ===
font_config = {
    "nama": {"path": "Futura-Bold.ttf", "size": 38},
    "departemen": {"path": "FUTURAMEDIUM.ttf", "size": 36},
    "level": {"path": "Futura.ttf", "size": 36},
    "employee_id": {"path": "FUTURAMEDIUM.ttf", "size": 36}
}

spacing_config = {
    "foto_to_nama": 20,
    "nama_to_departemen": 24,
    "departemen_to_level": 20,
    "level_to_employee_id": 20
}

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except IOError:
        print(f"⚠️ Font '{path}' tidak ditemukan. Menggunakan default.")
        return ImageFont.load_default()

fonts = {
    key: load_font(cfg["path"], cfg["size"])
    for key, cfg in font_config.items()
}

@app.route("/print", methods=["POST"])
def print_id_card():
    data = request.get_json()
    logging.info("📥 Received payload: %s", data)

    # Handle both single and batch payloads
    candidates = data if isinstance(data, list) else [data]
    results = []

    for candidate in candidates:
        try:
            nama = candidate.get("name")
            departemen = candidate.get("department")
            level = candidate.get("job_level")
            employee_id = candidate.get("employee_id")
            foto_filename = candidate.get("photo_filename")
            ctpat = candidate.get("ctpat")

            # File paths
            template_path = "Template.png"
            foto_dir = r"D:\sistem_cetak_idcard\pics\public\storage"
            if not foto_filename.lower().endswith(".jpeg"):
                foto_filename = foto_filename + ".jpeg"
            foto_path = os.path.join(foto_dir, foto_filename)
            output_file = f"{employee_id}_idcard.pdf"
            output_dir = r"D:\sistem_cetak_idcard\pics\public\storage\idcard"
            output_path = os.path.join(output_dir, output_file)

            # Cek apakah template, folder foto, dan file foto ada
            if not os.path.exists(template_path):
                results.append({
                    "employee_id": employee_id,
                    "status": "error",
                    "message": f"Template tidak ditemukan: {template_path}"
                })
                continue

            if not os.path.isdir(foto_dir):
                results.append({
                    "employee_id": employee_id,
                    "status": "error",
                    "message": f"Folder foto tidak ditemukan: {foto_dir}"
                })
                continue

            if not os.path.isfile(foto_path):
                results.append({
                    "employee_id": employee_id,
                    "status": "error",
                    "message": f"Foto tidak ditemukan: {foto_path}"
                })
                continue

            # Load template
            template = Image.open(template_path).convert('RGB')
            template_np = np.array(template)

            # Find yellow rectangle
            target_rgb = np.array([246, 255, 0])
            tolerance = 10
            mask = np.all(np.abs(template_np - target_rgb) <= tolerance, axis=-1).astype(np.uint8) * 255
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                results.append({
                    "employee_id": employee_id,
                    "status": "error",
                    "message": "❌ Kotak kuning tidak ditemukan dalam template."
                })
                continue

            x, y, w, h = cv2.boundingRect(contours[0])

            if not os.path.exists(foto_path):
                results.append({
                    "employee_id": employee_id,
                    "status": "error",
                    "message": f"Foto tidak ditemukan: {foto_filename}"
                })
                continue
            
            print(f"Foto : {foto_filename} ada")  # Tambahan: print jika foto ditemukan

            foto = Image.open(foto_path).resize((w, h))
            template.paste(foto, (x, y))

            draw = ImageDraw.Draw(template)

            def draw_centered_text(text, y_pos, font):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                draw.text((x + w // 2 - text_width // 2, y_pos), text, fill='black', font=font)
                return bbox[3] - bbox[1]

            current_y = y + h + spacing_config["foto_to_nama"]
            current_y += draw_centered_text(nama, current_y, fonts["nama"]) + spacing_config["nama_to_departemen"]
            current_y += draw_centered_text(departemen, current_y, fonts["departemen"]) + spacing_config["departemen_to_level"]
            current_y += draw_centered_text(level, current_y, fonts["level"]) + spacing_config["level_to_employee_id"]
            draw_centered_text(employee_id, current_y, fonts["employee_id"])
            
            template.save(output_path)
            
            local_path = output_path

            # Ubah backslash ke slash
            normalized_path = local_path.replace('\\', '/')

            # Ambil bagian setelah 'public/'
            relative_path = normalized_path.split('/public/')[-1]

            # Gabungkan dengan base URL
            base_url = 'http://10.10.19.42:8000/'
            full_url = base_url + relative_path

            results.append({
                "employee_id": employee_id,
                "status": "success",
                "output": full_url,
            })

        except Exception as e:
            results.append({
                "employee_id": candidate.get("employee_id", "unknown"),
                "status": "error",
                "message": str(e)
            })

    return jsonify(results), 200


if __name__ == "__main__":
    app.run(debug=True)
