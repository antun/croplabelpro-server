
from flask import Flask, request, jsonify
import requests
import json
import time

app = Flask(__name__)

# URL for the API request
api_url = "https://api.replicate.com/v1/predictions"

# Replace 'your_token_here' with your actual API token
api_token = "r8_4cAphiTVFDG2uiyIHBU0WLN3VxtGrTf17wKLL"

# Headers for the request
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {api_token}"
}

@app.route('/process-image', methods=['POST'])
def process_image():
    # Retrieve the image URL from the request
    data = request.get_json()
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

    # API request data
    api_data = {
        "version": "371aeee1ce0c5efd25bbef7a4527ec9e59188b963ebae1eeb851ddc145685c17",
        "input": {
            "iou": 0.9,
            "conf": 0.2,
            "retina": True,
            "box_prompt": "[0,0,0,0]",
            "image_size": 640,
            "model_name": "FastSAM-x",
            "input_image": image_url,
            "point_label": "[0]",
            "point_prompt": "[[0,0]]",
            "withContours": True,
            "better_quality": True
        }
    }

    # Send the prediction request
    response = requests.post(api_url, headers=headers, data=json.dumps(api_data))

    if response.status_code not in [200, 201]:
        return jsonify({"error": "Error sending prediction request", "details": response.text}), response.status_code

    prediction_id = response.json().get('id')

    # Check the prediction status
    while True:
        status_response = requests.get(f"{api_url}/{prediction_id}", headers=headers)
        if status_response.status_code == 200:
            result = status_response.json()
            if result.get('status') == 'succeeded':
                # Process the result as needed
                # For example, you can return the result or save the output image
                return jsonify(result), 200
        time.sleep(2)  # Add a delay between checks to avoid rate-limiting

    return jsonify({"message": "Processing complete"})

if __name__ == '__main__':
    app.run(debug=True)
