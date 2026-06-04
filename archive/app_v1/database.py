# Database.py
import sqlite3
import os
import pandas as pd

class Database:
    def __init__(self, db_name="yt_history.db"):
        self.db_name = db_name

    def save_to_database(self, watch_df, search_df):
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
        conn = sqlite3.connect(self.db_name)
        watch_df.to_sql("watch_history", conn, index=False)
        search_df.to_sql("search_history", conn, index=False)
        conn.close()
        print(f"\nSaved data to database '{self.db_name}' (overwrite mode)")

    def load_watch_search(self):
        """Load both watch_history and search_history as DataFrames"""
        if not os.path.exists(self.db_name):
            return pd.DataFrame(), pd.DataFrame()  # empty if DB doesn't exist
        conn = sqlite3.connect(self.db_name)
        try:
            watch_df = pd.read_sql("SELECT * FROM watch_history", conn, parse_dates=["time"])
        except Exception:
            watch_df = pd.DataFrame()
        try:
            search_df = pd.read_sql("SELECT * FROM search_history", conn, parse_dates=["time"])
        except Exception:
            search_df = pd.DataFrame()
        conn.close()
        return watch_df, search_df
