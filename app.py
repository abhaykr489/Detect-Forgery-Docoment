import os
import uuid
import time
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, send_from_directory
import cv2
import re
import pytesseract
import numpy as np
from PIL import Image, ImageChops

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['IMAGES_FOLDER'] = 'images'

@app.route('/')
def index():
    return render_template('index.html')

def has_unexpected_edges(edges):
    edge_threshold = 10
    if len(edges) > edge_threshold:
        return True  # Unexpected edges found
    else:
        return False  # No unexpected edges found

def has_inconsistencies(text):
    keywords = ['important', 'confidential', 'secret']
    for keyword in keywords:
        if keyword not in text:
            return True  # Inconsistencies found
    return False  # No inconsistencies found

def detect_scribbling_or_overwriting(text):
    # Implement your forgery detection logic based on OCR-detected text
    # For demonstration purposes, assume forgery detection based on specific data patterns

    # Example patterns for critical data fields (date, customer name, amount, invoice number)
    date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'  # Pattern for date (dd/mm/yyyy)
    name_pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'  # Pattern for full name (First Last)
    amount_pattern = r'\$\d+\.\d{2}\b'  # Pattern for currency amount ($XXX.XX)
    invoice_pattern = r'INV-\d{4}'  # Pattern for invoice number (INV-XXXX)

    # Check if any of the critical data patterns are found in the OCR-detected text
    date_match = re.search(date_pattern, text)
    name_match = re.search(name_pattern, text)
    amount_match = re.search(amount_pattern, text)
    invoice_match = re.search(invoice_pattern, text)

    # If any critical data pattern is not found, consider it a forgery
    if not (date_match and name_match and amount_match and invoice_match):
        print("Scribbling or overwriting forgery detected")
        return True  # Scribbling or overwriting forgery detected
    else:
        print("No scribbling or overwriting forgery detected")
        return False  # No scribbling or overwriting forgery detected

def detect_whitener_forgery(image_path):
    # Load the image in color mode
    color_image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if color_image is None:
        return False

    # Convert the color image to grayscale
    gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)

    # Set a threshold for whitener detection (adjust based on testing)
    whitener_threshold = 200

    # Count the number of pixels with intensity greater than the threshold manually
    whitener_pixel_count = np.sum(gray_image > whitener_threshold)

    # Set a threshold for the percentage of whitener pixels (adjust based on testing)
    whitener_percentage_threshold = 0.1

    # Calculate the percentage of whitener pixels in the image
    total_pixels = gray_image.size
    whitener_percentage = whitener_pixel_count / total_pixels

    # Check if the percentage of whitener pixels exceeds the threshold
    if whitener_percentage > whitener_percentage_threshold:
        print("whitener forgery detected")
    else:
        print("No whitner forgery")
    return whitener_percentage > whitener_percentage_threshold

#function to detect digital forgery
def detect_digital_forgery(image_path):
    original_image = Image.open(image_path)
    # Convert the image to RGB mode
    original_image = original_image.convert('RGB')
    # Save the original image in a temporary file
    original_image.save("original_temp2.jpg", quality=90)
    # Open the saved original image
    original_temp = Image.open("original_temp2.jpg")
    # Calculate Error Level Analysis (ELA)
    ela_image = ImageChops.difference(original_temp, original_image)
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    # Set a threshold for forgery detection (adjust based on testing)
    threshold = 40

    # Check if the maximum difference exceeds the threshold
    if max_diff > threshold:
        print("digital forgery detected")
    else:
        print("No digital forgery")
    return max_diff > threshold

#function to detect text alteration
def preprocess_image(image_path):
    # Read the image and apply preprocessing techniques
    image = cv2.imread(image_path)

    # Denoise the image
    denoised_image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 15)

    # Enhance contrast
    lab = cv2.cvtColor(denoised_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    contrast_enhanced_image = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    # Convert the enhanced image to grayscale
    gray_image = cv2.cvtColor(contrast_enhanced_image, cv2.COLOR_BGR2GRAY)

    # Thresholding to create a binary image
    _, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary_image

#function to detect data manipulation forgery
def detect_data_manipulation_forgery(image_path):
        # Perform OCR on the uploaded image
        preprocessed_image = preprocess_image(image_path)
        extracted_text = pytesseract.image_to_string(preprocessed_image)

        # Define regular expressions for critical data fields
        date_pattern = r'\b\d{2}/\d{2}/\d{4}\b'  # Pattern for date (dd/mm/yyyy)
        name_pattern = r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'  # Pattern for full name (First Last)
        amount_pattern = r'\$\d+\.\d{2}\b'  # Pattern for currency amount ($XXX.XX)
        invoice_pattern = r'INV-\d{4}'  # Pattern for invoice number (INV-XXXX)

        # Check if any of the critical data patterns are found in the extracted text
        date_match = re.search(date_pattern, extracted_text)
        name_match = re.search(name_pattern, extracted_text)
        amount_match = re.search(amount_pattern, extracted_text)
        invoice_match = re.search(invoice_pattern, extracted_text)

        # If any critical data pattern is not found, consider it a data manipulation forgery
        if not (date_match and name_match and amount_match and invoice_match):
            print("Data manipulation forgery detected")
            return True  # Data manipulation forgery detected
        else:
            print("No data manipulation forgery detected")
            return False  # No data manipulation forgery detected

def detect_text_alteration_forgery(image_path):
    uniformity_threshold = 0.9

    preprocessed_image = preprocess_image(image_path)

    # Perform OCR on the preprocessed image
    extracted_text = pytesseract.image_to_string(preprocessed_image)

    # Calculate uniformity of characters in the extracted text
    total_characters = len(extracted_text)
    unique_characters = len(set(extracted_text))

    if total_characters > 0:
        uniformity = unique_characters / total_characters

        # Compare uniformity with the threshold
        if uniformity < uniformity_threshold:
            print("Text alteration forgery detected")
            return True
        else:
            print("No text alteration forgery detected")
            return False
    else:
        print("No text detected or empty text. Skipping text alteration forgery check.")
        return False

# Function to detect and mark forgery
def detect_and_mark_forgery(original_path):
    scribbling_or_overwriting = detect_scribbling_or_overwriting(original_path)
    digital_forgery = detect_digital_forgery(original_path)
    whitener_detected = detect_whitener_forgery(original_path)
    text_alteration_forgery = detect_text_alteration_forgery(original_path)
    data_manipulation = detect_data_manipulation_forgery(original_path)

    unique_filename = None  # Default value for unique_filename
    forgery_types = []

    # Calculate the percentage of each type of forgery detected
    total_checks = 5  # Number of forgery detection methods
    detected_count = 0

    if scribbling_or_overwriting:
        forgery_types.append("Overwriting_Forgery")
        detected_count += 1

    if digital_forgery:
        forgery_types.append("Digital_Forgery")
        detected_count += 1

    if whitener_detected:
        forgery_types.append("Whitener_Forgery")
        detected_count += 1

    if text_alteration_forgery:
         forgery_types.append("Text_alteration_Forgery")
         detected_count += 1

    if data_manipulation:
         forgery_types.append("data_manipulation_Forgery")
         detected_count +=1

    # Calculate the percentage of forgery detected
    forgery_percentage = (detected_count / total_checks) * 100

    forgery_type = ", ".join(forgery_types)

    # Check if any forgery is detected
    if detected_count > 0:
        # Implement forgery marking logic here (e.g., draw colored rectangles or annotations)
        image = cv2.imread(original_path)
        forgery_area = (500, 500, 500, 500)  # Example forgery area: (x, y, width, height)
        x, y, w, h = forgery_area
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)  # Red color for forgery areas

        # Generate a unique filename using a timestamp and a UUID
        unique_filename = str(int(time.time())) + '_' + str(uuid.uuid4()) + '.jpg'

        # Convert image to RGB mode before saving as JPEG
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)

        # Save the marked image to the IMAGES_FOLDER
        marked_image_path = os.path.join(app.config['IMAGES_FOLDER'], unique_filename)
        pil_image.save(marked_image_path)  # Save the marked image as PNG

        return marked_image_path, forgery_percentage, forgery_type
    else:
    # No forgery detected
     print("No forgery detected")
     return original_path, 0, None

# Route for file upload
@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400  # Bad Request status code

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400  # Bad Request status code

        if file:
            filename = secure_filename(file.filename)  # Ensure a secure filename
            uploaded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(uploaded_image_path)

            # Detect forgery and get the marked image path and forgery type
            marked_image_path, forgery_percentage, forgery_type = detect_and_mark_forgery(uploaded_image_path)

            if forgery_type:
                # Prepare the response object with forgery type and percentage
                response = {
                    'message': 'Forgery detected successfully',
                    'forgery_image_path': marked_image_path,
                    'forgery_type': forgery_type,
                    'forgery_percentage': forgery_percentage,
                }
            else:
                # No forgery detected
                response = {
                    'message': 'No forgery detected',
                    'forgery_type': 'None',
                    'forgery_percentage': 0
                }

            return jsonify(response)
    except Exception as e:
            return jsonify({'error': str(e)}), 500  # Internal Server Error status code


# Route to serve uploaded images
@app.route('/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['IMAGES_FOLDER'], filename)

# Main function to run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
