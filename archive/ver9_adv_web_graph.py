import sqlite3
import pandas as pd
import textwrap
import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go

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

# Convert time to naive datetime if timezone exists
watch_df['time_naive'] = watch_df['time'].dt.tz_localize(None) if watch_df['time'].dt.tz else watch_df['time']

# ---------------------------
# Dash App
# ---------------------------
app = dash.Dash(__name__)
app.title = "YouTube History Dashboard"

# ---------------------------
# Top Channels Bar Chart
# ---------------------------
if 'channel_name' in watch_df.columns:
    channel_counts = watch_df['channel_name'].value_counts().head(10)
    channel_labels = [textwrap.fill(c, 20) for c in channel_counts.index]
    fig_channels = px.bar(
        x=channel_counts.values,
        y=channel_labels,
        orientation='h',
        labels={'x':'Videos Watched','y':'Channel'},
        title="Top Channels Watched",
        text=channel_counts.values
    )
    fig_channels.update_yaxes(autorange="reversed")

# ---------------------------
# Top Search Terms
# ---------------------------
if not search_df.empty:
    search_counts = search_df['title'].astype(str).str.lower().str.strip().value_counts().head(10)
    search_labels = [textwrap.fill(c, 20) for c in search_counts.index]
    fig_search = px.bar(
        x=search_counts.values,
        y=search_labels,
        orientation='h',
        labels={'x':'Search Count','y':'Search Term'},
        title="Top Search Terms",
        text=search_counts.values
    )
    fig_search.update_yaxes(autorange="reversed")

# ---------------------------
# Video Category Distribution Pie
# ---------------------------
if 'category_name' in watch_df.columns and not watch_df['category_name'].isna().all():
    category_counts = watch_df['category_name'].value_counts()
    small_pct_threshold = 0.02
    total = category_counts.sum()
    large = category_counts[category_counts / total >= small_pct_threshold].copy()
    small_sum = category_counts[category_counts / total < small_pct_threshold].sum()
    if small_sum > 0:
        large = pd.concat([large, pd.Series({'Others': small_sum})])
    large_sorted = large.sort_values(ascending=False)
    fig_category = px.pie(
        names=[textwrap.fill(c,15) for c in large_sorted.index],
        values=large_sorted.values,
        title="Video Category Distribution"
    )

# ---------------------------
# Daily Videos Watched Line Chart
# ---------------------------
if not watch_df.empty:
    watch_daily = watch_df.groupby(watch_df['time'].dt.date).size()
    fig_daily = px.line(
        x=watch_daily.index,
        y=watch_daily.values,
        labels={'x':'Date','y':'Videos Watched'},
        title="Daily Videos Watched"
    )

# ---------------------------
# Weekly Videos Watched
# ---------------------------
weekly_counts = watch_df.groupby([watch_df['time_naive'].dt.isocalendar().year,
                                  watch_df['time_naive'].dt.isocalendar().week]).size()
weekly_labels = [f"{y}-W{w:02d}" for y, w in weekly_counts.index]
fig_weekly = px.line(
    x=weekly_labels,
    y=weekly_counts.values,
    labels={'x':'Week','y':'Videos Watched'},
    title="Weekly Videos Watched"
)

# ---------------------------
# Category Prevalence Over Time (Stacked)
# ---------------------------
if 'category_name' in watch_df.columns and not watch_df.empty:
    counts = watch_df.groupby([pd.Grouper(key='time_naive', freq='W'),'category_name']).size().unstack(fill_value=0)
    threshold = 0.02
    total_per_category = counts.sum()
    small_categories = total_per_category[total_per_category / total_per_category.sum() < threshold].index
    if len(small_categories) > 0:
        counts['Others'] = counts[small_categories].sum(axis=1)
        counts.drop(columns=small_categories, inplace=True)
    counts = counts[counts.sum().sort_values(ascending=False).index]

    fig_cat_time = go.Figure()
    for col in counts.columns:
        fig_cat_time.add_trace(go.Scatter(
            x=counts.index, y=counts[col], mode='lines+markers', name=col
        ))
    fig_cat_time.update_layout(title="Category Prevalence Over Time (Weekly)",
                               xaxis_title="Week",
                               yaxis_title="Videos Watched")

# ---------------------------
# Search vs Watch Correlation
# ---------------------------
if not watch_df.empty and not search_df.empty:
    watch_counts_day = watch_df.groupby(watch_df['time'].dt.date).size()
    search_counts_day = search_df.groupby(search_df['time'].dt.date).size()
    df_corr = pd.concat([watch_counts_day, search_counts_day], axis=1).fillna(0)
    df_corr.columns = ['watch','search']
    fig_corr = px.scatter(df_corr, x='search', y='watch',
                          labels={'search':'Searches per Day','watch':'Videos Watched per Day'},
                          title="Search vs Watch Correlation")

# ---------------------------
# Layout
# ---------------------------
app.layout = html.Div([
    html.H1("YouTube History Dashboard", style={'textAlign':'center'}),
    dcc.Graph(figure=fig_channels),
    dcc.Graph(figure=fig_search),
    dcc.Graph(figure=fig_category),
    dcc.Graph(figure=fig_daily),
    dcc.Graph(figure=fig_weekly),
    dcc.Graph(figure=fig_cat_time),
    dcc.Graph(figure=fig_corr)
])

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
