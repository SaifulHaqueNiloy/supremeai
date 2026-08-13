import urllib.request, json

client_id = "9f2363cf-3cec-43f6-b155-a8625de19250"
client_secret = "84b1e22dd84b7227017f53414d68a36cad36d441463c85fdf4147219208c595f"
project_id = "92aa20c4-aef5-4e33-82bd-efb06058aaf0"

login_data = json.dumps({"clientId": client_id, "clientSecret": client_secret}).encode()
login_req = urllib.request.Request("https://app.infisical.com/api/v1/auth/universal-auth/login", data=login_data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(login_req) as res:
    token = json.loads(res.read().decode())["accessToken"]

secret_data = json.dumps({
    "workspaceId": project_id,
    "environment": "prod",
    "type": "shared",
    "secretValue": "Ov23liyGDYgVgGvpPy0Y",
    "secretPath": "/"
}).encode()
secret_req = urllib.request.Request("https://app.infisical.com/api/v3/secrets/raw/GITHUB_CLIENT_ID", data=secret_data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
try:
    with urllib.request.urlopen(secret_req) as res:
        print(res.read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode())
