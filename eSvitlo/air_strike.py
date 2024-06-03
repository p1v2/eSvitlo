import urllib.request
import os
import json

token = os.environ["ALERTS_API_TOKEN"]


def get_air_strike_oblasts():
    url = f"https://api.alerts.in.ua/v1/alerts/active.json?token={token}"

    oblasts = set()
    # no verify ssl
    with urllib.request.urlopen(url) as response:
        data = response.read()
        data_json = json.loads(data)

        for alert in data_json['alerts']:
            oblasts.add(alert['location_oblast'])

    return oblasts
