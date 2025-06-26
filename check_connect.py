from flask import Flask, jsonify
from flask import send_file
import os

app = Flask(__name__)

@app.route('/check_connect', methods=['GET'])
def check_connect():
    # send picture from path
    base_dir = r"D:\sistem_cetak_idcard\pics\public\storage"
    filename = "pic_1750662096.jpeg"
    image_path = os.path.join(base_dir, filename)
    return send_file(image_path, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(debug=True)