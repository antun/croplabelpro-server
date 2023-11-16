
from flask import Flask, request, jsonify
import requests
import json
import time
import uuid
from google.cloud import storage
import os
os.environ["GCLOUD_PROJECT"] = 'cropscanpro'


app = Flask(__name__)

# URL for the API request
api_url = "https://api.replicate.com/v1/deployments/antonelli182/hackathon-fastsam/predictions"

# Replace 'your_token_here' with your actual API token
api_token = "r8_4cAphiTVFDG2uiyIHBU0WLN3VxtGrTf17wKLL"

# Headers for the request
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {api_token}"
}

storage_client = storage.Client()
bucket_name = 'cropscanprobucket'


def error_json(message, details='', status_code=400):
    return jsonify({"status": "error", "message": message, "details": details}), status_code

def write_read(file_contents, bucket_name, blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.content_type = 'image/png'

    # Mode can be specified as wb/rb for bytes mode.
    # See: https://docs.python.org/3/library/io.html
    with blob.open("wb") as f:
        f.write(file_contents)


@app.route('/analyze', methods=['POST'])
def analyze(request):
    # Retrieve the image URL from the request
    data = request.get_json()
    rawImageUrl = data['rawImageUrl']

    if not rawImageUrl:
        return error_json("Missing 'rawImageUrl' parameter", '', 400)

    # Retrieve the image from the URL
    image_response = requests.get(rawImageUrl)
    # Save to GCS
    # Generate a random filename
    filename = 'rawImages/' + str(uuid.uuid4()) + '.png'
    write_read(image_response.content, bucket_name, filename)
    rawImageSavedUrl = f"https://storage.googleapis.com/cropscanprobucket/{filename}"

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
            "input_image": rawImageSavedUrl,
            "point_label": "[0]",
            "point_prompt": "[[0,0]]",
            "withContours": True,
            "better_quality": True
        }
    }

    # Send the prediction request
    response = requests.post(api_url, headers=headers, data=json.dumps(api_data))
    status_url = response.json().get('urls').get('get')

    if response.status_code not in [200, 201]:
        return error_json("Error sending prediction request", details, response.status_code)

    prediction_id = response.json().get('id')

    # Check the prediction status
    while True:
        status_response = requests.get(status_url, headers=headers)
        if status_response.status_code == 200:
            result = status_response.json()
            if result.get('status') == 'succeeded':
                # Process the result as needed
                # For example, you can return the result or save the output image
                return jsonify(
                    {
                        "status": "success",
                        "message": "Processing complete",
                        "rawImageUrl": rawImageUrl,
                        "rawImageSavedUrl": rawImageSavedUrl,
                        "segmentedImageUrl": result.get('output'),
                        "segments": [
                            { "color": "pink", "centerCoordinates": [[123,456]], "area": 12345 },
                            { "color": "blue", "centerCoordinates": [[457,456]], "area": 12345 }
                        ]
                    }
                ), 200
            elif result.get('status') == 'failed':
                print(result)
                return error_json("Error getting prediction response", '', status_response.status_code)
        else:
            return error_json("Error checking prediction status", status_response.json(), status_response.json())

        time.sleep(2)  # Add a delay between checks to avoid rate-limiting

