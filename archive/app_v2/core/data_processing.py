import json
import pandas as pd
import re

class DataProcessing:
    def __init__(self, json_file: str):
        self.json_file = json_file

    def flatten_data(self) -> pd.DataFrame:
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"[ERROR] File not found: {self.json_file}")
            return pd.DataFrame()
        except json.JSONDecodeError:
            print(f"[ERROR] Invalid JSON format: {self.json_file}")
            return pd.DataFrame()

        if isinstance(data, dict):
            data = data.get("items", data)

        flattened = []
        for entry in data:

            if not isinstance(entry, dict):
                continue

            row = {
                "header": entry.get("header"),
                "title": entry.get("title"),
                "title_url": entry.get("titleUrl"),
                "time": entry.get("time"),
                "description": entry.get("description"),
            }

            row["activity_controls"] = ", ".join(
                map(str, entry.get("activityControls", []))
            )

            row["products"] = ", ".join(
                map(str, entry.get("products", []))
            )

            details = entry.get("details", [])
            row["search_detail"] = (
                details[0].get("name")
                if isinstance(details, list) and len(details) > 0
                else None
            )

            subtitles = entry.get("subtitles", [])
            if isinstance(subtitles, list) and len(subtitles) > 0:
                row["channel_name"] = subtitles[0].get("name")
                row["channel_url"] = subtitles[0].get("url")
            else:
                row["channel_name"] = None
                row["channel_url"] = None

            flattened.append(row)

        df = pd.DataFrame(flattened)

        if "time" in df.columns:
            df["time"] = pd.to_datetime(df["time"], errors="coerce")

        df.rename(columns={"titleUrl": "title_url"}, inplace=True)

        df.dropna(how="all", inplace=True)

        return df

    @staticmethod
    def extract_video_id(url: str):
        """
        Extract video ID from YouTube URL formats.
        """

        if not url:
            return None

        patterns = [
            r"v=([^&]+)",             # standard watch URL
            r"youtu\.be/([^?&]+)",    # short URL
            r"embed/([^?&]+)"         # embed URL
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None