import matplotlib.pyplot as plt
import textwrap
import sqlite3
import pandas as pd
from matplotlib import rcParams
from matplotlib.dates import DateFormatter, WeekdayLocator

# ---------------------------
# Frequency Analysis from DB
# ---------------------------
def frequency_analysis(db_path="yt_history.db", top_n=10, wrap_chars=20, small_pct_threshold=0.02):
    """
    Generates visualizations from pre-populated YouTube history database.
    
    Charts included:
    - Top channels watched (horizontal bar)
    - Top search terms (horizontal bar)
    - Video category distribution (pie chart with small categories grouped as "Others")
    - Daily/weekly watch counts (line chart)
    - Search vs watch correlation (scatter plot)
    """
    
    # --- Load Data ---
    conn = sqlite3.connect(db_path)
    watch_df = pd.read_sql("SELECT * FROM watch_history", conn, parse_dates=["time"])
    search_df = pd.read_sql("SELECT * FROM search_history", conn, parse_dates=["time"])
    conn.close()
    
    # --- Setup fonts for Chinese / Unicode ---
    rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    rcParams['axes.unicode_minus'] = False
    
    # ---------------------------
    # 1. Top Channels Watched (Horizontal Bar)
    # ---------------------------
    if 'channel_name' in watch_df.columns:
        channel_counts = watch_df['channel_name'].value_counts().head(top_n)
        if not channel_counts.empty:
            labels = [textwrap.fill(label, wrap_chars) for label in channel_counts.index]
            plt.figure(figsize=(12, 6))
            plt.barh(range(len(channel_counts)), channel_counts.values, color='skyblue')
            plt.yticks(range(len(channel_counts)), labels)
            plt.gca().invert_yaxis()
            plt.xlabel("Number of Videos")
            plt.title("Top Channels Watched")
            plt.tight_layout()
            plt.show()
    
    # ---------------------------
    # 2. Top Search Terms (Horizontal Bar)
    # ---------------------------
    if not search_df.empty:
        search_counts = search_df['title'].astype(str).str.lower().str.strip().value_counts().head(top_n)
        if not search_counts.empty:
            labels = [textwrap.fill(label, wrap_chars) for label in search_counts.index]
            plt.figure(figsize=(12, 6))
            plt.barh(range(len(search_counts)), search_counts.values, color='salmon')
            plt.yticks(range(len(search_counts)), labels)
            plt.gca().invert_yaxis()
            plt.xlabel("Number of Searches")
            plt.title("Top Search Terms")
            plt.tight_layout()
            plt.show()
    
    # ---------------------------
    # 3. Video Category Distribution (Pie Chart with "Others")
    # ---------------------------
    if 'category_name' in watch_df.columns and not watch_df['category_name'].isna().all():
        category_counts = watch_df['category_name'].value_counts()
        total = category_counts.sum()
        
        # Split into large and small categories
        large = category_counts[category_counts / total >= small_pct_threshold].copy()
        small_sum = category_counts[category_counts / total < small_pct_threshold].sum()
        
    # Add "Others" explicitly if small_sum > 0
    if small_sum > 0:
        large = pd.concat([large, pd.Series({'Others': small_sum})])

    # Sort descending, but put "Others" at the end
    large_sorted = large.drop('Others', errors='ignore').sort_values(ascending=False)
    if 'Others' in large:
        large_sorted['Others'] = large['Others']

    plt.figure(figsize=(8,8))
    plt.pie(
        large_sorted.values,
        labels=[textwrap.fill(c, 15) for c in large_sorted.index],
        autopct='%1.1f%%',
        startangle=140,
        colors=plt.cm.tab20.colors[:len(large_sorted)]
    )
    plt.title("Video Category Distribution")
    plt.tight_layout()
    plt.show()
    
    # ---------------------------
    # 4. Daily Watch Counts (Line Chart)
    # ---------------------------
    if not watch_df.empty:
        watch_daily = watch_df.groupby(watch_df['time'].dt.date).size()
        plt.figure(figsize=(14,6))
        plt.plot(watch_daily.index, watch_daily.values, marker='o', linestyle='-', color='teal')
        
        # Format x-axis for better readability
        plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))  # Show max 10 date ticks
        plt.gcf().autofmt_xdate(rotation=45)
        
        plt.xlabel("Date")
        plt.ylabel("Videos Watched")
        plt.title("Daily Videos Watched")
        plt.tight_layout()
        plt.show()
        
        # ---------------------------
        # Weekly Watch Counts
        # ---------------------------
        if not watch_df.empty:
            # Convert to naive datetime to avoid timezone warning
            watch_df['time_naive'] = watch_df['time'].dt.tz_localize(None) if watch_df['time'].dt.tz else watch_df['time']
            
            # Aggregate by ISO year and week number
            weekly_counts = watch_df.groupby([
                watch_df['time_naive'].dt.isocalendar().year,
                watch_df['time_naive'].dt.isocalendar().week
            ]).size()
            
            # Create clean labels "YYYY-WW"
            labels = [f"{y}-W{w:02d}" for y, w in weekly_counts.index]
            
            plt.figure(figsize=(12,6))
            plt.plot(labels, weekly_counts.values, marker='o', linestyle='-', color='orange')
            
            # Show only every Nth week on x-axis
            tick_spacing = max(len(labels)//10, 1)  # roughly 10 ticks
            tick_indices = range(0, len(labels), tick_spacing)
            plt.xticks([labels[i] for i in tick_indices], rotation=45, ha='right')
            
            plt.xlabel("Week")
            plt.ylabel("Videos Watched")
            plt.title("Weekly Videos Watched")
            plt.tight_layout()
            plt.show()

    # ---------------------------
    # 5. Category Prevalence Over Time (Line Chart)
    # ---------------------------
    if 'category_name' in watch_df.columns and not watch_df.empty:
        # Use naive datetime
        watch_df['time_naive'] = watch_df['time'].dt.tz_localize(None) if watch_df['time'].dt.tz else watch_df['time']

        # Weekly aggregation
        counts = watch_df.groupby([pd.Grouper(key='time_naive', freq='W'), 'category_name']).size().unstack(fill_value=0)

        # Group small categories as "Others"
        threshold = 0.02
        total_per_category = counts.sum()
        small_categories = total_per_category[total_per_category / total_per_category.sum() < threshold].index
        if len(small_categories) > 0:
            counts['Others'] = counts[small_categories].sum(axis=1)
            counts.drop(columns=small_categories, inplace=True)

        # Sort categories by total frequency (legend order)
        total_per_category = counts.sum()
        counts = counts[total_per_category.sort_values(ascending=False).index]

        # Assign specific colors: main categories get unique colors, "Others" is grey
        main_categories = [c for c in counts.columns if c != "Others"]
        colors_list = plt.cm.tab20.colors[:len(main_categories)]
        category_colors = {cat: colors_list[i] for i, cat in enumerate(main_categories)}
        if "Others" in counts.columns:
            category_colors["Others"] = "grey"

        # Plotting
        plt.figure(figsize=(14,6))
        for col in counts.columns:
            plt.plot(counts.index, counts[col], marker='o', linestyle='-', label=col,
                    color=category_colors[col], alpha=0.8)

        # Format x-axis nicely
        tick_spacing = max(len(counts)//10, 1)
        tick_indices = range(0, len(counts), tick_spacing)
        tick_positions = [counts.index[i] for i in tick_indices]
        tick_labels = [counts.index[i].strftime('%Y-W%V') for i in tick_indices]
        plt.xticks(tick_positions, tick_labels, rotation=45, ha='right')

        plt.xlabel("Week")
        plt.ylabel("Videos Watched")
        plt.title("Category Prevalence Over Time (Weekly)")
        plt.legend(title="Category", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

    # ---------------------------
    # 6. Search vs Watch Correlation (Scatter Plot)
    # ---------------------------
    if not watch_df.empty and not search_df.empty:
        watch_counts = watch_df.groupby(watch_df['time'].dt.date).size()
        search_counts = search_df.groupby(search_df['time'].dt.date).size()
        df_corr = pd.DataFrame({'watch': watch_counts, 'search': search_counts}).fillna(0)
        
        plt.figure(figsize=(8,6))
        plt.scatter(df_corr['search'], df_corr['watch'], alpha=0.7, color='purple')
        plt.xlabel("Number of Searches per Day")
        plt.ylabel("Number of Videos Watched per Day")
        plt.title("Search vs Watch Correlation")
        plt.tight_layout()
        plt.show()

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    frequency_analysis("yt_history.db")
