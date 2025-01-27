from flask import Flask, request, jsonify, render_template, send_from_directory
from rembg import remove
from PIL import Image
from werkzeug.exceptions import RequestEntityTooLarge

import os
import io
import logging

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit

# Set up logging for error details
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'

# Error handler for large file uploads
@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(error):
    return jsonify({"error": "File size exceeds the maximum allowed limit of 5 MB"}), 413


# Make sure the folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify(error="No file part"), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify(error="No selected file"), 400

    try:
        # Read the file as a byte stream (instead of saving it immediately)
        image_bytes = file.read()

        # Try to open the image to check if it's a valid image file
        try:
            input_image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logging.error(f"Error opening image: {e}")
            return jsonify(error="Uploaded file is not a valid image."), 400

        # Process the image with rembg
        output_image = remove(input_image)

        # Generate a unique name for the output image and save it as PNG (supports transparency)
        output_filename = 'processed_' + file.filename.rsplit('.', 1)[0] + '.png'  # Force PNG extension
        output_path = os.path.join(PROCESSED_FOLDER, output_filename)
        output_image.save(output_path, format='PNG')  # Save in PNG format

        logging.info(f"Image processed successfully: {output_path}")
        # Return the output path to the front-end for displaying the image and enabling the download option
        return jsonify(message="Processing complete!", image_path=output_filename)

    except Exception as e:
        logging.error(f"Error processing the image: {str(e)}")
        return jsonify(error=f"Error processing the image: {str(e)}"), 500


@app.route('/processed/<filename>')
def download_image(filename):
    # Provide a route to download the processed image
    return send_from_directory(PROCESSED_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
