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
replicate_api_url = "https://api.replicate.com/v1/deployments/antonelli182/hackathon-fastsam/predictions"

replicate_api_token = "r8_4cAphiTVFDG2uiyIHBU0WLN3VxtGrTf17wKLL"

openai_api_key = os.environ.get("OPENAI_API_KEY", "OpenAI API key not set")

replicate_headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {replicate_api_token}"
}

response_headers = {
'Access-Control-Allow-Origin': '*'
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


def gpt_4_vision_api_call(segmented_image_url):
    # Payload for the GPT-4 Vision API call
    vision_payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Provide a numbered list of all colored segments (outlined with a blue contour), including high level position in the image, and its color. Just give the list, no other explanation/message."
                    },
                    {
                        "type": "image_url",
                        "image_url": {               
                            "url": segmented_image_url
                        }
                    }
                ]
            }
        ],
        "max_tokens": 800
    }
    openai_gpt4_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }
    # Making the GPT-4 Vision API call
    vision_response = requests.post("https://api.openai.com/v1/chat/completions", headers=openai_gpt4_headers, json=vision_payload)
    vision_response_data = vision_response.json()
    return vision_response_data


@app.route('/analyze', methods=['POST'])
def analyze(request):
    # Handle CORS
    if request.method == 'OPTIONS':
        # Allows POST requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, cors_headers)
    

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
    response = requests.post(replicate_api_url, headers=replicate_headers, data=json.dumps(api_data))
    status_url = response.json().get('urls').get('get')

    if response.status_code not in [200, 201]:
        return error_json("Error sending prediction request", details, response.status_code)

    prediction_id = response.json().get('id')

    # Check the prediction status
    while True:
        status_response = requests.get(status_url, headers=replicate_headers)
        if status_response.status_code == 200:
            result = status_response.json()
            if result.get('status') == 'succeeded':
                # Process the result as needed
                # For example, you can return the result or save the output image
                segmented_image_url = result.get('output')
                openai_vision_response = gpt_4_vision_api_call(segmented_image_url)
                choices = openai_vision_response.get('choices')[0].get('message').get('content')
                print('@choices', choices);

                return jsonify(
                    {
                        "status": "success",
                        "message": "Processing complete",
                        "rawImageUrl": rawImageUrl,
                        "rawImageSavedUrl": rawImageSavedUrl,
                        "segmentedImageUrl": segmented_image_url,
                        "segments": choices
                    }
                ), 200, response_headers
            elif result.get('status') == 'failed':
                print(result)
                return error_json("Error getting prediction response", '', status_response.status_code)
        else:
            return error_json("Error checking prediction status", status_response.json(), status_response.json())

        time.sleep(2)  # Add a delay between checks to avoid rate-limiting

