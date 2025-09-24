import sys
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
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl

# ---------------------------
# Load Data
# ---------------------------
def load_data(db_path="yt_history.db"):
    conn = sqlite3.connect(db_path)
    watch_df = pd.read_sql("SELECT * FROM watch_history", conn, parse_dates=["time"])
    search_df = pd.read_sql("SELECT * FROM search_history", conn, parse_dates=["time"])
    conn.close()
    return watch_df, search_df

watch_df, search_df = load_data()
watch_df['time_naive'] = watch_df['time'].dt.tz_localize(None) if watch_df['time'].dt.tz else watch_df['time']

# Prepare dropdown options
channels_options = [{'label': c, 'value': c} for c in watch_df['channel_name'].dropna().unique()]
categories_options = [{'label': c, 'value': c} for c in watch_df['category_name'].dropna().unique()]

# ---------------------------
# Dash App
# ---------------------------
app = dash.Dash(__name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"])

# ---------------------------
# Layout with compact filters
# ---------------------------
app.layout = html.Div([
    # YouTube-style title header
    html.Div([
        html.H1("YouTube History Dashboard", style={
            'color': 'white',
            'margin': '0',
            'fontFamily': 'Arial, sans-serif',
            'fontWeight': 'bold',
            'textAlign': 'center'
        })
    ], style={
        'backgroundColor': '#FF0000',   # YouTube red
        'padding': '15px 0',
        'boxShadow': '0 2px 5px rgba(0,0,0,0.3)',  # subtle card shadow
        'borderRadius': '5px',
        'marginBottom': '15px'
    }),

    # Filters row
    html.Div([
        # Date Range
        html.Div([
            html.Label("Date Range:", style={'fontSize':'12px'}),
            dcc.DatePickerRange(
                id='date-picker',
                min_date_allowed=watch_df['time_naive'].min().date(),
                max_date_allowed=watch_df['time_naive'].max().date(),
                start_date=watch_df['time_naive'].min().date(),
                end_date=watch_df['time_naive'].max().date(),
                display_format='YYYY-MM-DD',
                clearable=True,
                style={'fontSize':'12px'}
            )
        ], style={'marginRight':'15px'}),

        # Channel dropdown
        html.Div([
            html.Label("Channel:", style={'fontSize':'12px'}),
            dcc.Dropdown(
                id='channel-dropdown',
                options=[{'label':'All','value':'All'}]+channels_options,
                value='All',
                multi=False,
                clearable=False,
                style={'width':'180px', 'fontSize':'12px', 'lineHeight':'20px'}
            )
        ], style={'marginRight':'15px'}),

        # Category dropdown
        html.Div([
            html.Label("Category:", style={'fontSize':'12px'}),
            dcc.Dropdown(
                id='category-dropdown',
                options=[{'label':'All','value':'All'}]+categories_options,
                value='All',
                multi=False,
                clearable=False,
                style={'width':'180px', 'fontSize':'12px', 'lineHeight':'20px'}
            )
        ])
    ], style={
        'display':'flex',
        'alignItems':'center',
        'gap':'15px',
        'padding':'10px 5px',
        'position':'relative',
        'marginTop':'20px'
    }),


    # Tabs for charts
    dcc.Tabs([
        dcc.Tab(label='Top Channels', children=[dcc.Graph(id='fig-channels', style={'height':'400px'})]),
        dcc.Tab(label='Top Searches', children=[dcc.Graph(id='fig-search', style={'height':'400px'})]),
        dcc.Tab(label='Category Distribution', children=[dcc.Graph(id='fig-category', style={'height':'400px'})]),
        dcc.Tab(label='Daily Videos', children=[dcc.Graph(id='fig-daily', style={'height':'400px'})]),
        dcc.Tab(label='Weekly Videos', children=[dcc.Graph(id='fig-weekly', style={'height':'400px'})]),
        dcc.Tab(label='Category Over Time', children=[dcc.Graph(id='fig-cat-time', style={'height':'400px'})]),
        dcc.Tab(label='Search vs Watch', children=[dcc.Graph(id='fig-corr', style={'height':'400px'})])
    ], style={
        'fontSize':'12px',
        'marginTop':'20px',
        'marginBottom':'15px'
    })
])

# ---------------------------
# Callbacks for interactivity
# ---------------------------
@app.callback(
    Output('fig-channels', 'figure'),
    Output('fig-search', 'figure'),
    Output('fig-category', 'figure'),
    Output('fig-daily', 'figure'),
    Output('fig-weekly', 'figure'),
    Output('fig-cat-time', 'figure'),
    Output('fig-corr', 'figure'),
    Input('date-picker', 'start_date'),
    Input('date-picker', 'end_date'),
    Input('channel-dropdown', 'value'),
    Input('category-dropdown', 'value')
)
def update_charts(start_date, end_date, selected_channel, selected_category):
    # Use fallback if date picker is cleared
    start_date = pd.to_datetime(start_date) if start_date else watch_df['time_naive'].min()
    end_date = pd.to_datetime(end_date) if end_date else watch_df['time_naive'].max()

    # Filter watch_df and search_df by date
    mask = (watch_df['time_naive'].dt.date >= start_date.date()) & \
           (watch_df['time_naive'].dt.date <= end_date.date())
    filtered_watch = watch_df[mask].copy()

    mask_s = (search_df['time'].dt.date >= start_date.date()) & \
             (search_df['time'].dt.date <= end_date.date())
    filtered_search = search_df[mask_s].copy()

    # Filter by channel/category
    if selected_channel != 'All':
        filtered_watch = filtered_watch[filtered_watch['channel_name'] == selected_channel]
    if selected_category != 'All':
        filtered_watch = filtered_watch[filtered_watch['category_name'] == selected_category]

    # --- Top Channels ---
    if not filtered_watch.empty and 'channel_name' in filtered_watch.columns:
        channel_counts = filtered_watch['channel_name'].value_counts().head(10)
        labels = [textwrap.fill(c,20) for c in channel_counts.index]
        fig_channels = px.bar(x=channel_counts.values, y=labels, orientation='h', text=channel_counts.values,
                              labels={'x':'Videos Watched','y':'Channel'}, title="Top Channels Watched")
        fig_channels.update_yaxes(autorange="reversed")
    else:
        fig_channels = go.Figure()

    # --- Top Searches ---
    if not filtered_search.empty:
        search_counts = filtered_search['title'].astype(str).str.lower().str.strip().value_counts().head(10)
        labels = [textwrap.fill(c,20) for c in search_counts.index]
        fig_search = px.bar(x=search_counts.values, y=labels, orientation='h', text=search_counts.values,
                            labels={'x':'Search Count','y':'Search Term'}, title="Top Search Terms")
        fig_search.update_yaxes(autorange="reversed")
    else:
        fig_search = go.Figure()

    # --- Category Pie ---
    if 'category_name' in filtered_watch.columns and not filtered_watch.empty:
        category_counts = filtered_watch['category_name'].value_counts()
        total = category_counts.sum()
        small_sum = category_counts[category_counts/total < 0.02].sum()
        large = category_counts[category_counts/total >= 0.02].copy()
        if small_sum > 0:
            large = pd.concat([large, pd.Series({'Others': small_sum})])
        large_sorted = large.sort_values(ascending=False)
        fig_category = px.pie(names=[textwrap.fill(c,15) for c in large_sorted.index],
                              values=large_sorted.values,
                              title="Video Category Distribution")
    else:
        fig_category = go.Figure()

    # --- Daily Videos ---
    if not filtered_watch.empty:
        daily_counts = filtered_watch.groupby(filtered_watch['time_naive'].dt.date).size()
        fig_daily = px.line(x=daily_counts.index, y=daily_counts.values,
                            labels={'x':'Date','y':'Videos Watched'}, title="Daily Videos Watched")
    else:
        fig_daily = go.Figure()

    # --- Weekly Videos ---
    if not filtered_watch.empty:
        weekly_counts = filtered_watch.groupby([filtered_watch['time_naive'].dt.isocalendar().year,
                                                filtered_watch['time_naive'].dt.isocalendar().week]).size()
        weekly_labels = [f"{y}-W{w:02d}" for y,w in weekly_counts.index]
        fig_weekly = px.line(x=weekly_labels, y=weekly_counts.values,
                             labels={'x':'Week','y':'Videos Watched'}, title="Weekly Videos Watched")
    else:
        fig_weekly = go.Figure()

    # --- Category Over Time ---
    if not filtered_watch.empty:
        counts = filtered_watch.groupby([pd.Grouper(key='time_naive', freq='W'),'category_name']).size().unstack(fill_value=0)
        small_categories = counts.columns[(counts.sum()/counts.sum().sum())<0.02]
        if len(small_categories)>0:
            counts['Others'] = counts[small_categories].sum(axis=1)
            counts.drop(columns=small_categories, inplace=True)
        counts = counts[counts.sum().sort_values(ascending=False).index]
        fig_cat_time = go.Figure()
        for col in counts.columns:
            fig_cat_time.add_trace(go.Scatter(x=counts.index, y=counts[col], mode='lines+markers', name=col))
        fig_cat_time.update_layout(title="Category Prevalence Over Time (Weekly)",
                                   xaxis_title="Week", yaxis_title="Videos Watched")
    else:
        fig_cat_time = go.Figure()

    # --- Search vs Watch Correlation ---
    if not filtered_watch.empty and not filtered_search.empty:
        watch_day = filtered_watch.groupby(filtered_watch['time_naive'].dt.date).size()
        search_day = filtered_search.groupby(filtered_search['time'].dt.date).size()
        df_corr = pd.concat([watch_day, search_day], axis=1).fillna(0)
        df_corr.columns = ['watch','search']
        fig_corr = px.scatter(df_corr, x='search', y='watch',
                              labels={'search':'Searches per Day','watch':'Videos Watched per Day'},
                              title="Search vs Watch Correlation")
    else:
        fig_corr = go.Figure()

    return fig_channels, fig_search, fig_category, fig_daily, fig_weekly, fig_cat_time, fig_corr

# ---------------------------
# Run Dash in background thread
# ---------------------------
def run_dash():
    app.run(debug=False, port=8050)

threading.Thread(target=run_dash, daemon=True).start()

# ---------------------------
# PyQt6 Window
# ---------------------------
class DashWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Dashboard")
        self.setGeometry(100, 100, 1200, 900)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.wait_for_dash()

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

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    app_qt = QApplication(sys.argv)
    window = DashWindow()
    window.show()
    sys.exit(app_qt.exec())
