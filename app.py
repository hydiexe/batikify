import os
import io
import base64
import numpy as np
from PIL import Image
from flask import Flask, request, jsonify, render_template, send_from_directory

from tensorflow.keras.models import load_model
from tensorflow.keras.utils import custom_object_scope
from tensorflow.keras.layers import DepthwiseConv2D

app = Flask(__name__)

class CustomDepthwiseConv2D(DepthwiseConv2D):
    def __init__(self, **kwargs):
        if 'groups' in kwargs:
            del kwargs['groups']
        super().__init__(**kwargs)

try:
    with custom_object_scope({'DepthwiseConv2D': CustomDepthwiseConv2D}):
        model = load_model('model.h5', compile=False)
except OSError as e:
    print(f"Error loading model: {e}")
    print("Pastikan file 'model.h5' ada di direktori yang sama dengan app.py")
    model = None

BATIK_CLASSES = [
    "Batik Betawi", "Batik Bokor Kencono", "Batik Buketan", "Batik Dayak",
    "Batik Jlamprang", "Batik Kawung", "Batik Liong", "Batik Megamendung",
    "Batik Parang", "Batik Sekarjagat", "Batik Sidoluhur", "Batik Sidomukti",
    "Batik Sidomulyo", "Batik Singa Barong", "Batik Srikaton", "Batik Tribusono",
    "Batik Tujuh Rupa", "Batik Tuntrum", "Batik Wahyu Tumurun", "Batik Wirasat"
]
MODEL_INPUT_SIZE = (224, 224) 

def preprocess_image(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize(MODEL_INPUT_SIZE, Image.Resampling.LANCZOS)
    img_array = np.asarray(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js')

@app.route('/app', methods=['GET'])
def index_multi_page():
    return render_template('index_spa.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model tidak berhasil dimuat, periksa log server.'}), 500
    try:
        image_data = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'Tidak ada file yang dipilih'}), 400
            image_data = file.read()
        elif 'image_data' in request.form:
            base64_data = request.form['image_data'].split(',')[1]
            image_data = base64.b64decode(base64_data)
        if not image_data:
            return jsonify({'error': 'Data gambar tidak ditemukan'}), 400

        processed_image = preprocess_image(image_data)
        predictions = model.predict(processed_image)
        predicted_class_index = np.argmax(predictions[0])
        confidence = float(np.max(predictions[0]))
        predicted_class_name = BATIK_CLASSES[predicted_class_index]
        
        return jsonify({
            'prediction': predicted_class_name,
            'confidence': f"{confidence:.2%}"
        })
    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({'error': 'Terjadi kesalahan saat memproses gambar.'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
