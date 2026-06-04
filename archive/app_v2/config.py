import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=r"api_keys/YT_API_KEY.env")
API_KEY = os.getenv("YT_API_KEY")
DB_NAME = "yt_history.db"
DASH_PORT = 8050
DASH_URL = f"http://127.0.0.1:{DASH_PORT}"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, DB_NAME)

os.makedirs(DATA_DIR, exist_ok=True)