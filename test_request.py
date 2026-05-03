import requests
import time

url = "http://127.0.0.1/search"  # Replace with your target URL
num_requests = 15  # Set between 10 and 15

payload = {
  "query": "budget notebook for programming",
  "top_k": 10
}

headers = {
    "Content-Type": "application/json",
    # "Authorization": "Bearer YOUR_TOKEN",  # Uncomment if needed
}

for i in range(num_requests):
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Request {i+1}: Status {response.status_code}, Response: {response.text}")
    except requests.RequestException as e:
        print(f"Request {i+1}: Failed - {e}")

    time.sleep(1)  # Optional delay between requests