import os
import io
import base64
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_to_kindle_format(image):
    """Convert image to 8-bit grayscale PNG for Kindle e-ink display"""
    # Convert to grayscale (L mode = 8-bit grayscale)
    grayscale = image.convert('L')
    return grayscale

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Open and get image info
        with Image.open(filepath) as img:
            width, height = img.size
            # Convert to base64 for preview
            buffered = io.BytesIO()
            img_rgb = img.convert('RGB')
            img_rgb.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'width': width,
            'height': height,
            'preview': f'data:image/png;base64,{img_base64}'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/process', methods=['POST'])
def process_image():
    # Receive the already cropped and rotated image from Cropper.js
    if 'croppedImage' not in request.files:
        return jsonify({'error': 'No cropped image provided'}), 400
    
    file = request.files['croppedImage']
    
    try:
        img = Image.open(file.stream)
        
        # Convert to 8-bit grayscale for Kindle
        img_grayscale = convert_to_kindle_format(img)
        
        # Save the processed image
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'frame.png')
        img_grayscale.save(output_path, 'PNG')
        
        # Create preview
        buffered = io.BytesIO()
        img_grayscale.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'preview': f'data:image/png;base64,{img_base64}',
            'width': img_grayscale.width,
            'height': img_grayscale.height
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/frame.png')
def serve_frame():
    """Serve the processed image for Kindle to fetch"""
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'frame.png')
    if os.path.exists(output_path):
        return send_file(output_path, mimetype='image/png')
    else:
        # Return a placeholder or 404
        return "No image available", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8088, debug=True)
