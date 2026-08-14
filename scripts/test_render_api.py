import requests

RENDER_API_KEY = "rnd_S0H7uYcNWmqX3jcepMTBL9WXghGP"
SERVICE_ID = "srv-d9vbvoc9v7es738m3trg"

url = f"https://api.render.com/v1/services/{SERVICE_ID}/env-vars"
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {RENDER_API_KEY}"
}

# Try format 1
payload = [{"envVar": {"key": "TEST_KEY", "value": "TEST_VAL"}}]
print("Trying format 1 (envVar wrapper)...")
res1 = requests.put(url, headers=headers, json=payload)
print(res1.status_code, res1.text)

# Try format 2
payload = [{"key": "TEST_KEY", "value": "TEST_VAL"}]
print("Trying format 2 (direct)...")
res2 = requests.put(url, headers=headers, json=payload)
print(res2.status_code, res2.text)
