from flask import Flask, request, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def apply_ghibli_style(image_path):
    # Load image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Apply bilateral filter for smoothing
    smoothed = cv2.bilateralFilter(image, 9, 75, 75)
    
    # Convert to grayscale for edge detection
    gray = cv2.cvtColor(smoothed, cv2.COLOR_RGB2GRAY)
    
    # Edge detection
    edges = cv2.Canny(gray, 100, 200)
    
    # Dilate edges
    kernel = np.ones((2,2), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    # Invert edges
    edges = cv2.bitwise_not(edges)
    
    # Combine smoothed image with edges
    # Convert edges to 3 channels
    edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    # Blend
    result = cv2.addWeighted(smoothed, 0.8, edges_colored, 0.2, 0)
    
    # Adjust colors to pastel
    result = result.astype(np.float32)
    result = result * 1.2  # brighten
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # Save result
    result_path = os.path.join(app.config['UPLOAD_FOLDER'], 'result_' + os.path.basename(image_path))
    result_bgr = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
    cv2.imwrite(result_path, result_bgr)
    
    return result_path

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process image
            result_path = apply_ghibli_style(filepath)
            
            return render_template('result.html', original=filename, result=os.path.basename(result_path))
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)