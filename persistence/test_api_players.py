import requests

API_KEY = "brEyqEssHcgDFlyANbRxXLUAJAPYFkFitCURYyGxhpc331FYpJ4jt9KNddh6"
URL = "https://api.sportmonks.com/v3/football/players"

params = {
    "api_token": API_KEY,
    "page": 1,
    "include": "detailedPosition;team"
}

response = requests.get(URL, params=params)

print("STATUS:", response.status_code)
print("RAW RESPONSE:")
print(response.text)
