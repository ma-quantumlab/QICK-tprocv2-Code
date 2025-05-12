import plotly.graph_objs as go
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
from flask import request
import json
import datetime


def create_figure(name):
    fig = go.Figure()
    fig.update_layout(title=f"{name} (Created at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    fig.update_layout(uirevision=name)
    return fig


figure_ids = ['res_spec', 'qubit_spec', 'rabi', 'ramsey', 't1']
figures = {fig_id: create_figure(fig_id) for fig_id in figure_ids}

app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0),

    # single column
    # html.Div([dcc.Graph(id=fig_id, figure=figures[fig_id]) for fig_id in figure_ids])

    # two column
    html.Div([
        dcc.Graph(id='res_spec', figure=figures['res_spec']),
        dcc.Graph(id='qubit_spec', figure=figures['qubit_spec'])
    ], style={'columnCount': 3}),
    html.Br(),
    html.Div([
        dcc.Graph(id='rabi', figure=figures['rabi']),
        dcc.Graph(id='ramsey', figure=figures['ramsey']),
        dcc.Graph(id='t1', figure=figures['t1'])
    ], style={'columnCount': 3})
])


@app.server.route('/send_data', methods=['POST'])
def receive_data():
    data = json.loads(request.data)
    fig_id = data['fig_id']
    figure_json = data['figure']
    timestamp = data['timestamp']
    fitting_params = data['fitting_params']
    figure = go.Figure(figure_json)
    figure.update_layout(uirevision=timestamp)

    if fig_id in figure_ids:

        if figure['layout']['uirevision'] == figures[fig_id]['layout']['uirevision']:
            figure['layout'] = figures[fig_id]['layout']

        # Update the figure data and layout
        figures[fig_id] = figure

        fitting_params_text = ', '.join([f"{param}={fitting_params[param]:.2f}" for param in fitting_params])
        figures[fig_id].update_layout(
            title=f"{fig_id} (Updated at {datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')})",
            annotations=[
                go.layout.Annotation(
                    x=0.05,
                    y=0.95,
                    text=fitting_params_text,
                    showarrow=False,
                    font=dict(color='black', size=12),
                    xref='paper',
                    yref='paper',
                    align='left',
                    valign='top'
                )
            ]
        )
        return {'status': 'success'}
    else:
        return {'status': 'error', 'message': 'Invalid figure ID'}


@app.callback(
    [Output(fig_id, 'figure') for fig_id in figure_ids],
    [Input('interval-component', 'n_intervals')]
)
def update_figures(n_intervals):
    return [figures.get(fig_id) for fig_id in figure_ids]


if __name__ == '__main__':
    app.run_server(debug=True)

# import plotly.graph_objs as go
# import dash
# import dash_core_components as dcc
# import dash_html_components as html
# from dash.dependencies import Input, Output, State
# from flask import request
# import json
# import datetime
#
# def create_figure(name):
#     fig = go.Figure()
#     fig.update_layout(title=f"{name} (Created at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
#     return fig
#
# figure_ids = ['res_spec', 'qubit_spec', 'rabi', 'ramsey', 't1']
# figures = {fig_id: create_figure(fig_id) for fig_id in figure_ids}
#
# app = dash.Dash(__name__)
# app.layout = html.Div([
#     dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
#
#     # single column
#     # html.Div([dcc.Graph(id=fig_id, figure=figures[fig_id]) for fig_id in figure_ids])
#
#     # two column
#     html.Div([
#         dcc.Graph(id='res_spec', figure=figures['res_spec']),
#         dcc.Graph(id='qubit_spec', figure=figures['qubit_spec'])
#     ], style={'columnCount': 3}),
#     html.Br(),
#     html.Div([
#         dcc.Graph(id='rabi', figure=figures['rabi']),
#         dcc.Graph(id='ramsey', figure=figures['ramsey']),
#         dcc.Graph(id='t1', figure=figures['t1'])
#     ], style={'columnCount': 3})
# ])
#
# @app.server.route('/send_data', methods=['POST'])
# def receive_data():
#     data = json.loads(request.data)
#     fig_id = data['fig_id']
#     figure_json = data['figure']
#     timestamp = data['timestamp']
#     fitting_params = data['fitting_params']
#     figure = go.Figure(figure_json)
#
#     if fig_id in figure_ids:
#         figures[fig_id] = figure
#         fitting_params_text = ', '.join([f"{param}={fitting_params[param]:.2f}" for param in fitting_params])
#         figures[fig_id].update_layout(
#             title=f"{fig_id} (Updated at {datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')})",
#             annotations=[
#                 go.layout.Annotation(
#                     x=0.05,
#                     y=0.95,
#                     text=fitting_params_text,
#                     showarrow=False,
#                     font=dict(color='black', size=12),
#                     xref='paper',
#                     yref='paper',
#                     align='left',
#                     valign='top'
#                 )
#             ]
#         )
#         return {'status': 'success'}
#     else:
#         return {'status': 'error', 'message': 'Invalid figure ID'}
#
# @app.callback(
#     [Output(fig_id, 'figure') for fig_id in figure_ids],
#     [Input('interval-component', 'n_intervals')]
# )
# def update_figures(n_intervals):
#     return [figures.get(fig_id) for fig_id in figure_ids]
#
# if __name__ == '__main__':
#     app.run_server(debug=True)
