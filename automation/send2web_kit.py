import requests
import numpy as np
import json
import plotly.graph_objs as go
import time

def send_figure(fig_id, data):
    url = "http://127.0.0.1:8050/send_data"
    payload = {
        "fig_id": fig_id,
        "figure": json.loads(data['figure_json']),
        "timestamp": data['timestamp'],
        "fitting_params": data['fitting_params']
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()