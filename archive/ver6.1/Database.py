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
