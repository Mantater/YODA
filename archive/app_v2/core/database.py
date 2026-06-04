import sqlite3
import os
import pandas as pd
from app.config import DB_PATH


class Database:
    def __init__(self):
        self.db_path = DB_PATH
        print("DB PATH:", self.db_path)

    def save_to_database(self, watch_df, search_df):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        conn = sqlite3.connect(self.db_path)
        watch_df.to_sql("watch_history", conn, index=False)
        search_df.to_sql("search_history", conn, index=False)
        conn.close()

        print(f"\nSaved data to database '{self.db_path}' (overwrite mode)")

    def load_watch_search(self):
        if not os.path.exists(self.db_path):
            return pd.DataFrame(), pd.DataFrame()

        conn = sqlite3.connect(self.db_path)

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