# Dashboard.py
import os
import threading
import time
import requests
import sqlite3
import pandas as pd
import textwrap
import dash
from dash import dcc, html, Output, Input
import plotly.express as px
import plotly.graph_objects as go
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from app.config import DB_PATH

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Web view
        self.browser = QWebEngineView()
        self.layout.addWidget(self.browser)

        self.dash_started = False
        self.start_dash()
        self.dash_started = True

    def load_data(self):
        if not os.path.exists(DB_PATH):
            return pd.DataFrame(), pd.DataFrame()

        try:
            conn = sqlite3.connect(DB_PATH)

            watch_df = pd.read_sql(
                "SELECT * FROM watch_history",
                conn,
                parse_dates=["time"]
            )

            search_df = pd.read_sql(
                "SELECT * FROM search_history",
                conn,
                parse_dates=["time"]
            )

            conn.close()

            if not watch_df.empty:
                watch_df["time_naive"] = watch_df["time"].dt.tz_localize(None)

            return watch_df, search_df

        except Exception as e:
            print(f"[Dashboard] Failed to load data: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def start_dash(self):
        self.watch_df, self.search_df = self.load_data()

        # Safely prepare dropdown options
        channels_options = (
            [{'label': c, 'value': c} for c in self.watch_df['channel_name'].dropna().unique()]
            if not self.watch_df.empty and 'channel_name' in self.watch_df.columns else []
        )

        categories_options = (
            [{'label': c, 'value': c} for c in self.watch_df['category_name'].dropna().unique()]
            if not self.watch_df.empty and 'category_name' in self.watch_df.columns else []
        )

        self.app = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])
        self.app.layout = self.get_layout(channels_options, categories_options)

        self.register_callbacks()

        threading.Thread(
            target=lambda: self.app.run(debug=False, port=8050, use_reloader=False),
            daemon=True
        ).start()

        self.wait_for_dash()

    def get_layout(self, channels_options, categories_options):

        title_div = html.Div(
            html.H1(
                "YODA Dashboard",
                style={
                    'color': 'white',
                    'margin': '0',
                    'fontFamily': 'Arial, sans-serif',
                    'fontWeight': 'bold',
                    'textAlign': 'center'
                }
            ),
            style={
                'backgroundColor': '#FF0000',
                'padding': '15px 0',
                'boxShadow': '0 2px 5px rgba(0,0,0,0.3)',
                'borderRadius': '5px',
                'marginBottom': '15px'
            }
        )

        return html.Div([
            # Title
            title_div,

            # No data banner
            html.Div(
                id="no-data-banner",
                children="",
                style={
                    "textAlign": "center",
                    "color": "#d32f2f",
                    "fontSize": "16px",
                    "fontFamily": "Segoe UI, Arial",
                    "marginTop": "15px",
                    "padding": "12px",
                    "borderRadius": "10px",
                    "backgroundColor": "#ffeaea",
                    "display": "none"   # hidden by default
                }
            ),

            # Filters
            html.Div([
                html.Div([
                    html.Label("Date Range:", style={'fontSize': '12px'}),
                    dcc.DatePickerRange(
                        id='date-picker',
                        min_date_allowed=pd.Timestamp("2000-01-01"),
                        max_date_allowed=pd.Timestamp.today(),
                        start_date=None,
                        end_date=None,
                        display_format='YYYY-MM-DD',
                        clearable=True,
                        style={'fontSize': '12px'}
                    )
                ], style={'marginRight': '15px'}),

                html.Div([
                    html.Label("Channel:", style={'fontSize': '12px'}),
                    dcc.Dropdown(
                        id='channel-dropdown',
                        options=[{'label': 'All', 'value': 'All'}],
                        value='All',
                        multi=False,
                        clearable=False,
                        style={'width': '180px', 'fontSize': '12px'}
                    )
                ], style={'marginRight': '15px'}),

                html.Div([
                    html.Label("Category:", style={'fontSize': '12px'}),
                    dcc.Dropdown(
                        id='category-dropdown',
                        options=[{'label': 'All', 'value': 'All'}],
                        value='All',
                        multi=False,
                        clearable=False,
                        style={'width': '180px', 'fontSize': '12px'}
                    )
                ])
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'gap': '15px',
                'padding': '10px 5px',
                'marginTop': '20px'
            }),

            # Tabs
            dcc.Tabs([
                dcc.Tab(label='Top Channels', children=[dcc.Graph(id='fig-channels', style={'height': '400px'})]),
                dcc.Tab(label='Top Searches', children=[dcc.Graph(id='fig-search', style={'height': '400px'})]),
                dcc.Tab(label='Category Distribution', children=[dcc.Graph(id='fig-category', style={'height': '400px'})]),
                dcc.Tab(label='Daily Videos', children=[dcc.Graph(id='fig-daily', style={'height': '400px'})]),
                dcc.Tab(label='Weekly Videos', children=[dcc.Graph(id='fig-weekly', style={'height': '400px'})]),
                dcc.Tab(label='Category Over Time', children=[dcc.Graph(id='fig-cat-time', style={'height': '400px'})]),
                dcc.Tab(label='Search vs Watch', children=[dcc.Graph(id='fig-corr', style={'height': '400px'})])
            ], style={
                'fontSize': '12px',
                'marginTop': '20px',
                'marginBottom': '15px'
            })

        ])

    def register_callbacks(self):

        # Dropdowns (channels + category)
        @self.app.callback(
            Output('channel-dropdown', 'options'),
            Output('category-dropdown', 'options'),
            Input('date-picker', 'id')  # trigger on load
        )
        def update_dropdowns(_):
            watch_df, _ = self.load_data()

            if watch_df.empty:
                return (
                    [{'label': 'All', 'value': 'All'}],
                    [{'label': 'All', 'value': 'All'}]
                )

            channels = [{'label': 'All', 'value': 'All'}] + [
                {'label': c, 'value': c}
                for c in sorted(watch_df['channel_name'].dropna().unique())
            ]

            categories = [{'label': 'All', 'value': 'All'}] + [
                {'label': c, 'value': c}
                for c in sorted(watch_df['category_name'].dropna().unique())
            ]

            return channels, categories

        # Date picker range
        @self.app.callback(
            Output('date-picker', 'min_date_allowed'),
            Output('date-picker', 'max_date_allowed'),
            Output('date-picker', 'start_date'),
            Output('date-picker', 'end_date'),
            Input('date-picker', 'id')  # trigger on load
        )
        def update_date_picker(_):
            watch_df, _ = self.load_data()

            if watch_df.empty:
                today = pd.Timestamp.today().date()
                return today, today, None, None

            min_date = watch_df['time_naive'].min().date()
            max_date = watch_df['time_naive'].max().date()

            return min_date, max_date, min_date, max_date

        # Charts + banner
        @self.app.callback(
            Output('fig-channels', 'figure'),
            Output('fig-search', 'figure'),
            Output('fig-category', 'figure'),
            Output('fig-daily', 'figure'),
            Output('fig-weekly', 'figure'),
            Output('fig-cat-time', 'figure'),
            Output('fig-corr', 'figure'),
            Output('no-data-banner', 'children'),
            Output('no-data-banner', 'style'),
            Input('date-picker', 'start_date'),
            Input('date-picker', 'end_date'),
            Input('channel-dropdown', 'value'),
            Input('category-dropdown', 'value'),
            Input('date-picker', 'id')  # Crit trigger
        )
        def update_charts(start_date, end_date, selected_channel, selected_category, _):

            watch_df, search_df = self.load_data()

            # No data vase
            if watch_df.empty and search_df.empty:
                empty = go.Figure()
                return (
                    empty, empty, empty, empty, empty, empty, empty,
                    "No data available. Please upload watch and search history.",
                    {
                        "display": "block",
                        "textAlign": "center",
                        "color": "#d32f2f",
                        "fontSize": "16px",
                        "fontFamily": "Segoe UI, Arial",
                        "marginTop": "15px",
                        "padding": "12px",
                        "borderRadius": "10px",
                        "backgroundColor": "#ffeaea"
                    }
                )

            # Date filter
            if not watch_df.empty:
                start_date = pd.to_datetime(start_date) if start_date else watch_df['time_naive'].min()
                end_date = pd.to_datetime(end_date) if end_date else watch_df['time_naive'].max()

                mask = (
                    (watch_df['time_naive'].dt.date >= start_date.date()) &
                    (watch_df['time_naive'].dt.date <= end_date.date())
                )
                filtered_watch = watch_df[mask].copy()
            else:
                filtered_watch = watch_df

            if not search_df.empty:
                mask_s = (
                    (search_df['time'].dt.date >= start_date.date()) &
                    (search_df['time'].dt.date <= end_date.date())
                )
                filtered_search = search_df[mask_s].copy()
            else:
                filtered_search = search_df

            # Filters
            if selected_channel != 'All' and not filtered_watch.empty:
                filtered_watch = filtered_watch[filtered_watch['channel_name'] == selected_channel]

            if selected_category != 'All' and not filtered_watch.empty:
                filtered_watch = filtered_watch[filtered_watch['category_name'] == selected_category]

            # --- Charts ---
            fig_channels = go.Figure()
            fig_search = go.Figure()
            fig_category = go.Figure()
            fig_daily = go.Figure()
            fig_weekly = go.Figure()
            fig_cat_time = go.Figure()
            fig_corr = go.Figure()

            # Top Channels
            if not filtered_watch.empty and 'channel_name' in filtered_watch:
                counts = filtered_watch['channel_name'].value_counts().head(10)
                fig_channels = px.bar(x=counts.values, y=counts.index, orientation='h')
                fig_channels.update_yaxes(autorange="reversed")

            # Top Searches
            if not filtered_search.empty:
                counts = filtered_search['title'].value_counts().head(10)
                fig_search = px.bar(x=counts.values, y=counts.index, orientation='h')
                fig_search.update_yaxes(autorange="reversed")

            # Category Pie
            if not filtered_watch.empty and 'category_name' in filtered_watch:

                category_counts = filtered_watch['category_name'].value_counts()

                total = category_counts.sum()

                threshold = 0.02    # threshold (2%)
                large = category_counts[category_counts / total >= threshold]
                small = category_counts[category_counts / total < threshold].sum()

                if small > 0:
                    large["Others"] = small

                fig_category = px.pie(
                    names=large.index,
                    values=large.values,
                    title="Category Distribution"
                )

            # Daily Trend
            if not filtered_watch.empty:
                daily = filtered_watch.groupby(filtered_watch['time_naive'].dt.date).size()
                fig_daily = px.line(x=daily.index, y=daily.values)

            # Weekly Trend
            if not filtered_watch.empty:

                weekly = (
                    filtered_watch
                    .set_index('time_naive')
                    .resample('W')
                    .size()
                )

                fig_weekly = px.line(
                    x=weekly.index,
                    y=weekly.values,
                    labels={"x": "Week", "y": "Videos Watched"},
                    title="Weekly Videos Watched"
                )

                fig_weekly.update_xaxes(
                    tickformat="%Y-%m",
                    tickangle=45
                )

            # Category Over Time
            if not filtered_watch.empty:

                grouped = filtered_watch.groupby(
                    [pd.Grouper(key='time_naive', freq='W'), 'category_name']
                ).size().unstack(fill_value=0)

                # ---- collapse small categories ----
                threshold = 0.02

                col_totals = grouped.sum()
                total = col_totals.sum()

                small_cols = col_totals[col_totals / total < threshold].index
                large_cols = col_totals[col_totals / total >= threshold].index

                grouped_large = grouped[large_cols].copy()

                if len(small_cols) > 0:
                    grouped_large["Others"] = grouped[small_cols].sum(axis=1)

                # ---- plot ----
                fig_cat_time = go.Figure()

                for col in grouped_large.columns:
                    fig_cat_time.add_trace(
                        go.Scatter(
                            x=grouped_large.index,
                            y=grouped_large[col],
                            mode="lines+markers",
                            name=col
                        )
                    )

            # Search vs Watch Correlation
            if not filtered_watch.empty and not filtered_search.empty:
                w = filtered_watch.groupby(filtered_watch['time_naive'].dt.date).size()
                s = filtered_search.groupby(filtered_search['time'].dt.date).size()
                df_corr = pd.concat([w, s], axis=1).fillna(0)
                df_corr.columns = ['watch', 'search']
                fig_corr = px.scatter(df_corr, x='search', y='watch')

            banner = ""  # hide banner when data exists
            style = {"display": "none"}

            return (
                fig_channels, fig_search, fig_category,
                fig_daily, fig_weekly, fig_cat_time, fig_corr,
                banner, style
            )
    
    def wait_for_dash(self):
        url = "http://127.0.0.1:8050"
        while True:
            try:
                r = requests.get(url)
                if r.status_code == 200:
                    break
            except:
                pass
            time.sleep(0.1)
        self.browser.setUrl(QUrl(url))

    def reload_data(self):
        self.load_data()
        self.browser.reload()