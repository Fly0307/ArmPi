# import requests
# payload = dict(key1='value1', key2='value2')
# r = requests.post('https://httpbin.org/post', data=payload)
# print(r.text)
# client.py
import requests
import random
url = "http://localhost:9030"

# Generate a random number of length 13
id = random.randint(10**12, 10**13-1)
# Example using method 'echo'
payload = {
    "method": "LoadFunc",
    "params": [2],
    "jsonrpc": "2.0",
    "id": id,
}
headers = {'Content-Type': 'text/x-markdown'}
response = requests.post(url, json=payload, headers=headers).json()

print(response)

# Generate a random number of length 13
id = random.randint(10**12, 10**13-1)
# Example using method 'echo'
payload = {
    "method": "StartFunc",
    "params": [],
    "jsonrpc": "2.0",
    "id": id,
}
headers = {'Content-Type': 'text/x-markdown'}
response = requests.post(url, json=payload, headers=headers).json()

print(response)

id = random.randint(10**12, 10**13-1)
payload = {
    "method": "ColorTracking",
    "params": ["red"],
    "jsonrpc": "2.0",
    "id": id,
}
headers = {'Content-Type': 'text/x-markdown'}
response = requests.post(url, json=payload, headers=headers).json()

print(response)
# # Example using method 'add'
# payload = {
#     "method": "add",
#     "params": [1, 2],
#     "jsonrpc": "2.0",
#     "id": 0,
# }
# response = requests.post(url, json=payload, headers=headers).json()

# print(response)

# # Example using method 'foobar'
# payload = {
#     "method": "foobar",
#     "params": {"foo": 1, "bar": 2},
#     "jsonrpc": "2.0",
#     "id": 0,
# }
# response = requests.post(url, json=payload, headers=headers).json()

# print(response)
