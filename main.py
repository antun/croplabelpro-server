
from flask import Flask, request, jsonify
import requests
import json
import time

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

def error_json(message, details='', status_code=400):
    return jsonify({"status": "error", "message": message, "details": details}), status_code

@app.route('/analyze', methods=['POST'])
def analyze(request):
    # Retrieve the image URL from the request
    data = request.get_json()
    print('data.rawImageUrl', data['rawImageUrl'])
    rawImageUrl = data['rawImageUrl']

    if not rawImageUrl:
        return error_json("Missing 'rawImageUrl' parameter", '', 400)

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
            "input_image": rawImageUrl,
            "point_label": "[0]",
            "point_prompt": "[[0,0]]",
            "withContours": True,
            "better_quality": True
        }
    }

    print('Sending prediction request...')
    # Send the prediction request
    response = requests.post(api_url, headers=headers, data=json.dumps(api_data))
    status_url = response.json().get('urls').get('get')
    print('Got prediction response', response.json())
    print('status_url', status_url)

    if response.status_code not in [200, 201]:
        return error_json("Error sending prediction request", details, response.status_code)

    prediction_id = response.json().get('id')
    print('prediction_id', prediction_id)

    # Check the prediction status
    while True:
        status_response = requests.get(status_url, headers=headers)
        print('status_response', status_response)
        print('status_response', status_response.json())
        if status_response.status_code == 200:
            result = status_response.json()
            if result.get('status') == 'succeeded':
                # Process the result as needed
                # For example, you can return the result or save the output image
                return jsonify(
                    {
                        "status": "success",
                        "message": "Processing complete",
                        "rawImageUrl": "https://maps.googleapis.com/maps/api/staticmap?size=640x480&maptype=satellite&center=-19.608607231997194,-45.991371645484705&key=AIzaSyBj92vPkR0DBR6emjqohYXorNPVePsUl5o&zoom=17&scale=2",
                        "segmentedImageUrl": result.get('output'),
                        "segments": [
                            { "color": "pink", "centerCoordinates": [[123,456]], "area": 12345 },
                            { "color": "blue", "centerCoordinates": [[457,456]], "area": 12345 }
                        ]
                    }
                ), 200
            elif result.get('status') == 'failed':
                return error_json("Error getting prediction response", '', status_response.status_code)
        else:
            return error_json("Error checking prediction status", status_response.json(), status_response.json())

        time.sleep(2)  # Add a delay between checks to avoid rate-limiting

