import urllib.request
import json
import sys

try:
    req = urllib.request.Request("http://localhost:8002/api/status")
    with urllib.request.urlopen(req, timeout=2) as response:
        print(response.read().decode())
except Exception as e:
    print("Error:", e)
