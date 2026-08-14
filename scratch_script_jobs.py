import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')
req = urllib.request.Request('https://api.github.com/repos/SaifulHaqueNiloy/supremeai/actions/runs/31719416674/jobs')
req.add_header('Accept', 'application/vnd.github.v3+json')
try:
    with urllib.request.urlopen(req) as response:
        jobs = json.loads(response.read().decode())['jobs']
        for j in jobs:
            if j['conclusion'] == 'failure':
                print('Failed Job:', j['name'])
                for step in j['steps']:
                    if step['conclusion'] == 'failure':
                        print('  Failed Step:', step['name'])
except Exception as e:
    print('Error fetching jobs:', e)
