import requests
import json

# Assuming the FastAPI server is running on localhost:8000
url = "http://127.0.0.1:8000/extract-relics/"

# Path to the video file
video_path = "/Users/graham/Documents/Development/nightreign-relics/videos/test.mp4"

# Request payload
payload = {"video_path": video_path, "start_second": 0}

# Send the POST request
response = requests.post(url, json=payload)

# Check the response
if response.status_code == 200:
    print("Request successful!")
    print("Response:")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"Request failed with status code: {response.status_code}")
    print("Response:")
    print(response.text)
