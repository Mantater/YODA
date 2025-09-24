import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load API key from .env
load_dotenv(dotenv_path=r"api_keys/YT_API_KEY.env")
API_KEY = os.getenv("YT_API_KEY")

print("API_KEY:", API_KEY)

if not API_KEY:
    raise ValueError("⚠️ API key not found! Check your .env file.")

youtube = build("youtube", "v3", developerKey=API_KEY)
print("YouTube client ready!")