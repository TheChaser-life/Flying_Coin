import http.client
import json

conn = http.client.HTTPConnection('localhost', 8000)
headers = {'Content-Type': 'application/json'}
body = json.dumps({'ticker': 'BTCUSDT', 'initial_capital': 10000})
conn.request('POST', '/api/v1/backtest/run', body=body, headers=headers)
res = conn.getresponse()
print(f'Status: {res.status}')
print(res.read().decode())
