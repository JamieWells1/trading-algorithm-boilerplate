import sys
import os

from dash import Dash, html, dcc, Input, Output

import build as graph
import api.fetch as api

config = api.get_settings()

app = Dash(
    __name__,
    external_stylesheets=[
        "https://cdn.jsdelivr.net/npm/bootswatch@5.1.3/dist/cyborg/bootstrap.min.css"
    ],
)
server = app.server

app.layout = html.Div([
    dcc.Graph(id="candles", style={"height": "125vh"}),
    dcc.Interval(id="interval", interval=86400000),
])


@app.callback(
    Output("candles", "figure"),
    Input("interval", "n_intervals"),
)
def update_graph(n_intervals):
    try:
        if config["general"]["simulate"]:
            return graph.simulate()
        else:
            return graph.build()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(f"\nGraph failed to load: {e} => {exc_type, fname, exc_tb.tb_lineno}\n")
        raise


def main():
    app.run(debug=True)
