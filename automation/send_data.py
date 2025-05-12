import requests
import numpy as np
import json
import plotly.graph_objs as go
import time

def create_figure_with_fitted_data(x, y, name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=name))

    # Add fitted data and fitting parameters as an example
    fitted_y = np.sin(x)  # Replace this with your actual fitted data
    fig.add_trace(go.Scatter(x=x, y=fitted_y, mode='lines', name='Fitted data'))
    fitting_params = {'A': 1, 'B': 2}  # Replace A and B with your actual fitting parameters

    return {
        'figure_json': fig.to_json(),
        'timestamp': time.time(),
        'fitting_params': fitting_params
    }

def send_figure(fig_id, data):
    url = "http://localhost:8050/send_data"
    payload = {
        "fig_id": fig_id,
        "figure": json.loads(data['figure_json']),
        "timestamp": data['timestamp'],
        "fitting_params": data['fitting_params']
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

# Example usage:
figure_ids = ['res_spec', 'qubit_spec', 'rabi', 'ramsey', 't1']

for fig_id in figure_ids:
    x, y = np.linspace(0, 2 * np.pi, 100), np.sin(np.linspace(0, 2 * np.pi, 100)) + np.random.normal(0, 0.1, 100)
    data = create_figure_with_fitted_data(x, y, fig_id)
    response = send_figure(fig_id, data)
    print(response)

