import requests
import time

# OpenAI API Key
api_key = "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"

# Headers for API requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

headersAssistant = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}",
    "OpenAI-Beta": "assistants=v1"
}

# Function to check the status of the run
def check_run_status(thread_id, run_id):
    response = requests.get(f"https://api.openai.com/v1/threads/{thread_id}/runs/{run_id}", headers=headersAssistant)
    return response.json()

# Function to poll for run completion
def poll_run_completion(thread_id, run_id, interval=5, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        run_status = check_run_status(thread_id, run_id)
        if run_status['status'] == 'completed':
            return run_status
        elif run_status['status'] in ['failed', 'cancelled', 'expired']:
            raise Exception(f"Run ended with status: {run_status['status']}")
        time.sleep(interval)
    raise TimeoutError("Run did not complete within the specified timeout.")

# Payload for the GPT-4 Vision API call
vision_payload = {
    "model": "gpt-4-vision-preview",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Provide a bullet list of all colored segments (outlined with a blue contour), including high level position in the image, and its color. Just give the list, no other explanation/message."
                },
                {
                    "type": "image_url",
                    "image_url": {               
                        "url": "https://www.mentha.red/misc/out.jpg"
                    }
                }
            ]
        }
    ],
    "max_tokens": 800
}

# Making the GPT-4 Vision API call
vision_response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=vision_payload)
vision_response_data = vision_response.json()
#print(vision_response_data)

# Extracting the text response from the vision API
AI_text_response = vision_response_data['choices'][0]['message']['content']

# Payload for the Assistant API call
assistant_payload = {
    "assistant_id": "asst_qVGwKu0Sg7nubSYC74LxfEfK",  # Replace with your actual assistant ID
    "thread": {
        "messages": [
            {"role": "user", "content": "based on the following segments, ask the user to tell you what crop and when planted each of them: "+ AI_text_response}
        ]
    }
}

# Making the Assistant API call
assistant_response = requests.post("https://api.openai.com/v1/threads/runs", headers=headersAssistant, json=assistant_payload)
assistant_response_data = assistant_response.json()

# Additional payload for the new API call
new_message_payload = {
    "role": "user",
    "content": "Green segment is coffee."
}

def parse_thread_messages(response):
    # Extract the list of messages
    messages = response['data']
    
    # Initialize a list to store the parsed messages
    parsed_messages = []

    # Loop through each message and extract the content and role
    for message in messages:
        # Extract the role of the sender
        role = message['role']

        # Extract the message content, which is in a list of dictionaries
        content_list = message['content']
        
        # Each item in the content list is a dictionary; we extract the 'value' from the 'text' key
        for content in content_list:
            if 'text' in content:
                text_content = content['text']['value']
                parsed_messages.append((role, text_content))

    return parsed_messages

# URL for the new API call
thread_url = "https://api.openai.com/v1/threads/"+assistant_response_data["thread_id"]+"/messages"

# Check if the run has been queued or is in progress
if assistant_response_data['status'] in ['queued', 'in_progress']:
    try:
        completed_run_data = poll_run_completion(assistant_response_data['thread_id'], assistant_response_data['id'])
        new_message_response = requests.post(thread_url, headers=headersAssistant, json=new_message_payload)

        new_message_response_data = new_message_response.json()

        messages_list = requests.get(thread_url, headers=headersAssistant)
        parsed_messages = parse_thread_messages(messages_list.json())

        for role, message in parsed_messages:
            print(f"{role}: {message}")

        #print(new_message_response_data)

    except Exception as e:
        print("Error while waiting for run to complete:", e)
else:
    print("Run did not start correctly. Status:", assistant_response_data['status'])