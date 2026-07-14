import urllib.request, json, os

token = ''
with open('.env', 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('GITHUB_TOKEN='):
            token = line.split('=', 1)[1].strip().strip('\"').strip('\'')
            break

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github.v3+json'}
req = urllib.request.Request('https://api.github.com/repos/paykaribazaronline/supremeai/actions/runs/29347144368/jobs', headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        for job in data.get('jobs', []):
            if job['conclusion'] == 'failure':
                print(f"Failed Job: {job['name']}")
                for step in job['steps']:
                    if step['conclusion'] == 'failure':
                        print(f"  Failed Step: {step['name']}")
except Exception as e:
    print(e)
