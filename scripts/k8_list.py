import requests

# using service account 'robot' token
url = "https://console.pathfinder.gov.bc.ca:8443/oapi/v1"
headers = {"Authorization": "<robot-token>"}
r = requests.get(url, headers=headers, verify=False)

print(r.text)
# base64url.bearer.authorization.k8s.io.<token> undefined
