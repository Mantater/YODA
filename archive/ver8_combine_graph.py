import matplotlib.pyplot as plt
import textwrap
import sqlite3
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

# ---------------------------
# Frequency Analysis from DB
# ---------------------------
def frequency_analysis_scrollable(db_path="yt_history.db", top_n=10, wrap_chars=20, small_pct_threshold=0.02):
    """
    Generates all visualizations in a single scrollable Tkinter window.
    """
    # --- Load Data ---
    conn = sqlite3.connect(db_path)
    watch_df = pd.read_sql("SELECT * FROM watch_history", conn, parse_dates=["time"])
    search_df = pd.read_sql("SELECT * FROM search_history", conn, parse_dates=["time"])
    conn.close()

    # --- Setup fonts for Chinese / Unicode ---
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    # --- Tkinter Setup ---
    root = tk.Tk()
    root.title("YouTube History Analysis")

    # Scrollable Frame
    container = ttk.Frame(root)
    canvas = tk.Canvas(container, width=1000, height=800)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.pack(fill="both", expand=True)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # ---------------------------
    # Helper to add figure to scrollable frame
    def add_figure(fig):
        canvas_widget = FigureCanvasTkAgg(fig, master=scrollable_frame)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(pady=10)

    # ---------------------------
    # 1. Top Channels Watched
    if 'channel_name' in watch_df.columns:
        channel_counts = watch_df['channel_name'].value_counts().head(top_n)
        if not channel_counts.empty:
            labels = [textwrap.fill(label, wrap_chars) for label in channel_counts.index]
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.barh(range(len(channel_counts)), channel_counts.values, color='skyblue')
            ax.set_yticks(range(len(channel_counts)))
            ax.set_yticklabels(labels)
            ax.invert_yaxis()
            ax.set_xlabel("Number of Videos")
            ax.set_title("Top Channels Watched")
            fig.tight_layout()
            add_figure(fig)

    # ---------------------------
    # 2. Top Search Terms
    if not search_df.empty:
        search_counts = search_df['title'].astype(str).str.lower().str.strip().value_counts().head(top_n)
        if not search_counts.empty:
            labels = [textwrap.fill(label, wrap_chars) for label in search_counts.index]
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.barh(range(len(search_counts)), search_counts.values, color='salmon')
            ax.set_yticks(range(len(search_counts)))
            ax.set_yticklabels(labels)
            ax.invert_yaxis()
            ax.set_xlabel("Number of Searches")
            ax.set_title("Top Search Terms")
            fig.tight_layout()
            add_figure(fig)

    # ---------------------------
    # 3. Video Category Distribution
    if 'category_name' in watch_df.columns and not watch_df['category_name'].isna().all():
        category_counts = watch_df['category_name'].value_counts()
        total = category_counts.sum()
        large = category_counts[category_counts / total >= small_pct_threshold].copy()
        small_sum = category_counts[category_counts / total < small_pct_threshold].sum()
        if small_sum > 0:
            large = pd.concat([large, pd.Series({'Others': small_sum})])
        large_sorted = large.drop('Others', errors='ignore').sort_values(ascending=False)
        if 'Others' in large:
            large_sorted['Others'] = large['Others']

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(
            large_sorted.values,
            labels=[textwrap.fill(c, 15) for c in large_sorted.index],
            autopct='%1.1f%%',
            startangle=140,
            colors=plt.cm.tab20.colors[:len(large_sorted)]
        )
        ax.set_title("Video Category Distribution")
        fig.tight_layout()
        add_figure(fig)

    # ---------------------------
    # 4. Daily Watch Counts
    if not watch_df.empty:
        watch_daily = watch_df.groupby(watch_df['time'].dt.date).size()
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(watch_daily.index, watch_daily.values, marker='o', linestyle='-', color='teal')
        ax.set_xlabel("Date")
        ax.set_ylabel("Videos Watched")
        ax.set_title("Daily Videos Watched")
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()
        add_figure(fig)

    # ---------------------------
    # 5. Weekly Watch Counts
    if not watch_df.empty:
        watch_df['time_naive'] = watch_df['time'].dt.tz_localize(None) if watch_df['time'].dt.tz else watch_df['time']
        weekly_counts = watch_df.groupby([
            watch_df['time_naive'].dt.isocalendar().year,
            watch_df['time_naive'].dt.isocalendar().week
        ]).size()
        labels = [f"{y}-W{w:02d}" for y, w in weekly_counts.index]
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(labels, weekly_counts.values, marker='o', linestyle='-', color='orange')
        tick_spacing = max(len(labels)//10, 1)
        tick_indices = range(0, len(labels), tick_spacing)
        ax.set_xticks([labels[i] for i in tick_indices])
        ax.set_xticklabels([labels[i] for i in tick_indices], rotation=45, ha='right')
        ax.set_xlabel("Week")
        ax.set_ylabel("Videos Watched")
        ax.set_title("Weekly Videos Watched")
        fig.tight_layout()
        add_figure(fig)

    # ---------------------------
    # 6. Category Prevalence Over Time
    if 'category_name' in watch_df.columns and not watch_df.empty:
        counts = watch_df.groupby([pd.Grouper(key='time_naive', freq='W'), 'category_name']).size().unstack(fill_value=0)
        threshold = 0.02
        total_per_category = counts.sum()
        small_categories = total_per_category[total_per_category / total_per_category.sum() < threshold].index
        if len(small_categories) > 0:
            counts['Others'] = counts[small_categories].sum(axis=1)
            counts.drop(columns=small_categories, inplace=True)
        total_per_category = counts.sum()
        counts = counts[total_per_category.sort_values(ascending=False).index]

        main_categories = [c for c in counts.columns if c != "Others"]
        colors_list = plt.cm.tab20.colors[:len(main_categories)]
        category_colors = {cat: colors_list[i] for i, cat in enumerate(main_categories)}
        if "Others" in counts.columns:
            category_colors["Others"] = "grey"

        fig, ax = plt.subplots(figsize=(12, 5))
        for col in counts.columns:
            ax.plot(counts.index, counts[col], marker='o', linestyle='-', label=col, color=category_colors[col], alpha=0.8)

        tick_spacing = max(len(counts)//10, 1)
        tick_indices = range(0, len(counts), tick_spacing)
        tick_positions = [counts.index[i] for i in tick_indices]
        tick_labels = [counts.index[i].strftime('%Y-W%V') for i in tick_indices]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(tick_labels, rotation=45, ha='right')
        ax.set_xlabel("Week")
        ax.set_ylabel("Videos Watched")
        ax.set_title("Category Prevalence Over Time (Weekly)")
        ax.legend(title="Category", bbox_to_anchor=(1.05, 1), loc='upper left')
        fig.tight_layout()
        add_figure(fig)

    # ---------------------------
    # 7. Search vs Watch Correlation
    if not watch_df.empty and not search_df.empty:
        watch_counts = watch_df.groupby(watch_df['time'].dt.date).size()
        search_counts = search_df.groupby(search_df['time'].dt.date).size()
        df_corr = pd.concat([watch_counts, search_counts], axis=1).fillna(0)
        df_corr.columns = ['watch', 'search']

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(df_corr['search'], df_corr['watch'], alpha=0.7, color='purple')
        ax.set_xlabel("Number of Searches per Day")
        ax.set_ylabel("Number of Videos Watched per Day")
        ax.set_title("Search vs Watch Correlation")
        fig.tight_layout()
        add_figure(fig)

    root.mainloop()


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    frequency_analysis_scrollable("yt_history.db")
