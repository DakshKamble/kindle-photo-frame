import os
import io
import base64
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure app settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['OUTPUT_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')

# Ensure all responses have the correct content type
@app.after_request
def add_header(response):
    if request.path.startswith('/upload') or request.path.startswith('/process'):
        response.headers['Content-Type'] = 'application/json'
    return response

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

KINDLE_WIDTH = 600
KINDLE_HEIGHT = 800

def convert_to_kindle_format(image):
    """Convert image to 8-bit grayscale PNG for Kindle e-ink display (600x800)"""
    # Resize to Kindle screen dimensions
    image = image.resize((KINDLE_WIDTH, KINDLE_HEIGHT), Image.Resampling.LANCZOS)
    # Convert to grayscale (L mode = 8-bit grayscale)
    grayscale = image.convert('L')
    return grayscale

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part', 'success': False}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file', 'success': False}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Open and get image info
            with Image.open(filepath) as img:
                width, height = img.size
                # Convert to base64 for preview - use JPEG for smaller size
                buffered = io.BytesIO()
                img_rgb = img.convert('RGB')
                img_rgb.save(buffered, format="JPEG", quality=85, optimize=True)
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return jsonify({
                'success': True,
                'filename': filename,
                'width': width,
                'height': height,
                'preview': f'data:image/jpeg;base64,{img_base64}'
            })
        except Exception as e:
            app.logger.error(f"Error processing upload: {str(e)}")
            return jsonify({'error': str(e), 'success': False}), 500
    
    return jsonify({'error': 'Invalid file type', 'success': False}), 400

@app.route('/process', methods=['POST'])
def process_image():
    # Receive the already cropped and rotated image from Cropper.js
    if 'croppedImage' not in request.files:
        return jsonify({'error': 'No cropped image provided', 'success': False}), 400
    
    file = request.files['croppedImage']
    
    try:
        img = Image.open(file.stream)
        
        # Convert to 8-bit grayscale for Kindle
        img_grayscale = convert_to_kindle_format(img)
        
        # Create preview - use JPEG for smaller size
        buffered = io.BytesIO()
        img_grayscale.save(buffered, format="JPEG", quality=85, optimize=True)
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Save the optimized PNG for Kindle
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'frame.png')
        img_grayscale.save(output_path, format="PNG", optimize=True, compress_level=9)
        
        return jsonify({
            'success': True,
            'preview': f'data:image/jpeg;base64,{img_base64}',
            'width': img_grayscale.width,
            'height': img_grayscale.height
        })
    except Exception as e:
        app.logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/frame.png')
def serve_frame():
    """Serve the processed image for Kindle to fetch"""
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'frame.png')
    if os.path.exists(output_path):
        response = send_file(output_path, mimetype='image/png')
        # Add cache control headers
        response.headers['Cache-Control'] = 'public, max-age=300'  # Cache for 5 minutes
        return response
    else:
        # Return a placeholder or 404
        return "No image available", 404

if __name__ == '__main__':
    # Add support for proxies like ngrok
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Disable debug mode for production/ngrok use
    # Debug mode adds significant overhead and slows down requests
    app.run(host='0.0.0.0', port=8088, debug=False, threaded=True)
