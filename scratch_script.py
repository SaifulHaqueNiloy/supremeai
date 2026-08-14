import urllib.request, json
req = urllib.request.Request('https://api.github.com/repos/SaifulHaqueNiloy/supremeai/actions/runs?status=failure&per_page=1')
req.add_header('Accept', 'application/vnd.github.v3+json')
try:
    with urllib.request.urlopen(req) as response:
        runs = json.loads(response.read().decode())['workflow_runs']
        if runs:
            print('Latest failed run ID:', runs[0]['id'])
            print('HTML URL:', runs[0]['html_url'])
        else:
            print('No failed runs found.')
except Exception as e:
    print('Error fetching runs:', e)
