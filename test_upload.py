import requests

print('Testing upload endpoint...')
url = 'http://localhost:8000/api/graph/upload'
try:
    with open('api.md', 'rb') as f:
        files = {'file': ('api.md', f)}
        data = {'group_id': 'api_docs'}
        response = requests.post(url, files=files, data=data, timeout=30)

    print(f'Upload Status: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print('Upload successful!')
        print(f'Group ID used: api_docs')
        print(f'Document ID: {result.get("document_id")}')
        print(f'Nodes created: {result.get("nodes_created")}')
        print(f'Edges created: {result.get("edges_created")}')
        print(f'Processing time: {result.get("processing_time_seconds"):.1f}s')
    else:
        print(f'Upload failed: {response.text}')
except Exception as e:
    print(f'Error: {e}')

