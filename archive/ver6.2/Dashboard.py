from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import QUrl
import dash
from dash import dcc, html
import plotly.express as px
import threading
import flask
import pandas as pd

# Dummy data for now
df = pd.DataFrame({
    "Category": ["Music", "Gaming", "Education", "Comedy"],
    "Count": [50, 30, 20, 15]
})

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Flask server
        self.server = flask.Flask(__name__)
        self.dash_app = dash.Dash(__name__, server=self.server, url_base_pathname='/dash/')

        fig = px.bar(df, x="Category", y="Count", title="Watch History Overview")

        self.dash_app.layout = html.Div([
            html.H1("YouTube Dashboard"),
            dcc.Graph(figure=fig)
        ])

        # Start Dash in background thread
        threading.Thread(target=lambda: self.server.run(port=8050, debug=False, use_reloader=False)).start()

        # Embed in Qt WebEngine
        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl("http://127.0.0.1:8050/dash/"))
        layout.addWidget(self.webview)
