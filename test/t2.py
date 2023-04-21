import requests
import time

start = time.time()
response = requests.get("http://localhost:5000/ping")
end = time.time()

print(f"Response: {response.text}")
print(f"Round-trip time: {end - start} seconds")