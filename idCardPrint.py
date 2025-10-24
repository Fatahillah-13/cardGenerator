from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# === Font Config ===
font_config = {
    "nama": {"path": "Futura-Bold.ttf", "size": 38, "letter_spacing": 4},
    "departemen": {"path": "FUTURAMEDIUM.TTF", "size": 36, "letter_spacing": 2},
    "level": {"path": "Futura.ttf", "size": 24, "letter_spacing": 2},
    "employee_id": {"path": "FUTURAMEDIUM.TTF", "size": 36, "letter_spacing": 2}
}

spacing_config = {
    "foto_to_nama": 20,
    "nama_to_departemen": 34,
    "departemen_to_level": 24,
    "level_to_employee_id": 24
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

    candidates = data if isinstance(data, list) else [data]
    results = []
    pages = []

    for candidate in candidates:
        try:
            nama = candidate.get("name")
            departemen = candidate.get("department")
            level = candidate.get("job_level")
            employee_id = candidate.get("employee_id")
            foto_filename = candidate.get("photo_filename")
            card_template = candidate.get("card_template")

            # File paths
            template_path = r"C:\apps\Photo ID Card System\pics\public\\" + card_template
            foto_dir = r"C:\apps\Photo ID Card System\pics\public\storage"
            root, ext = os.path.splitext(foto_filename)
            if ext.lower() != ".jpg":
                foto_filename = root + ".jpg"
            foto_path = os.path.join(foto_dir, foto_filename)

            if not foto_filename or not isinstance(foto_filename, str):
                results.append({
                    "employee_id": employee_id,
                    "status": "error",
                    "message": "foto_filename is missing or not a valid string."
                })
                continue

            # if not foto_filename.lower().endswith(".jpeg"):
            #     foto_filename = foto_filename + ".jpeg"
            # foto_path = os.path.join(foto_dir, foto_filename)

            # Cek template dan foto
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

            # Load template dan cari kotak kuning
            template = Image.open(template_path).convert('RGB')
            template_np = np.array(template)

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

            foto = Image.open(foto_path).resize((w, h))
            template.paste(foto, (x, y))

            draw = ImageDraw.Draw(template)

            def draw_centered_text(text, y_pos, font, letter_spacing=0):
                # Draw text with custom letter spacing
                total_width = 0
                char_widths = []
                for char in text:
                    bbox = draw.textbbox((0, 0), char, font=font)
                    width = bbox[2] - bbox[0]
                    char_widths.append(width)
                    total_width += width
                total_width += letter_spacing * (len(text) - 1)
                start_x = x + w // 2 - total_width // 2
                current_x = start_x
                for i, char in enumerate(text):
                    draw.text((current_x, y_pos), char, fill='black', font=font)
                    current_x += char_widths[i] + letter_spacing
                # Return height
                bbox = draw.textbbox((0, 0), text, font=font)
                return bbox[3] - bbox[1]

            current_y = y + h + spacing_config["foto_to_nama"]
            current_y += draw_centered_text(nama, current_y, fonts["nama"], font_config["nama"].get("letter_spacing", 0)) + spacing_config["nama_to_departemen"]
            current_y += draw_centered_text(departemen, current_y, fonts["departemen"], font_config["departemen"].get("letter_spacing", 0)) + spacing_config["departemen_to_level"]
            current_y += draw_centered_text(level, current_y, fonts["level"], font_config["level"].get("letter_spacing", 0)) + spacing_config["level_to_employee_id"]
            draw_centered_text(employee_id, current_y, fonts["employee_id"], font_config["employee_id"].get("letter_spacing", 0))

            template = template.convert("RGB")
            pages.append(template)
            results.append({
                "employee_id": employee_id,
                "status": "success"
            })

        except Exception as e:
            results.append({
                "employee_id": candidate.get("employee_id", "unknown"),
                "status": "error",
                "message": str(e)
            })

    # Simpan semua ID Card ke dalam 1 PDF
    if pages:
        output_dir = r"C:\apps\Photo ID Card System\pics\public\storage\idcard"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_filename = f"idcards_batch_{timestamp}.pdf"
        output_path = os.path.join(output_dir, output_filename)

        pages[0].save(output_path, save_all=True, append_images=pages[1:], format="PDF")

        # Bangun URL
        normalized_path = output_path.replace("\\", "/")
        relative_path = normalized_path.split('/public/')[-1]
        base_url = 'http://10.10.100.193:8400/'
        full_url = base_url + relative_path

        results.insert(0, {
            "status": "success",
            "combined_output": full_url,
            "total_idcards": len(pages)
        })

    return jsonify(results), 200

if __name__ == "__main__":
    app.run(debug=True)
