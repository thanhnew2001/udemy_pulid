from flask import Flask, render_template, request, jsonify
import os
import replicate
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Cấu hình thư mục lưu trữ ảnh upload và ảnh kết quả
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/output'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Thiết lập các folder nếu chưa tồn tại
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Kiểm tra loại tệp hợp lệ
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API PulID trên Replicate
REPLICATE_MODEL = "zsxkib/pulid:43d309c37ab4e62361e5e29b8e9e867fb2dcbcec77ae91206a8d95ac5dd451a0"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file part"}), 400

    image = request.files['image']
    prompt = request.form.get('prompt')

    # Kiểm tra file có hợp lệ không
    if image.filename == '' or not allowed_file(image.filename):
        return jsonify({"error": "Invalid image file"}), 400

    # Lưu tệp hình ảnh vào thư mục uploads
    filename = secure_filename(image.filename)
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path)

    # Chuyển đổi hình ảnh thành URL để sử dụng trong API
    image_url = f'http://localhost:5000/{image_path}'

    # Tạo yêu cầu tới API Replicate
    input_data = {
        "prompt": prompt,
        "main_face_image": image_url
    }

    # Gọi API của PulID
    try:
        output = replicate.run(REPLICATE_MODEL, input=input_data)
        
        # Lưu các hình ảnh trả về từ API
        saved_images = []
        for index, item in enumerate(output):
            # Tạo tên tệp duy nhất
            unique_filename = f"{uuid.uuid4().hex}.webp"
            output_path = os.path.join(OUTPUT_FOLDER, unique_filename)
            
            with open(output_path, 'wb') as file:
                file.write(item.read())
            
            saved_images.append(f'/static/output/{unique_filename}')
        
        return jsonify({"images": saved_images})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
