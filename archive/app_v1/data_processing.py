import json
import pandas as pd
import re

class DataProcessing:
    def __init__(self, json_file):
        self.json_file = json_file

    def flatten_data(self):
        with open(self.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        flattened = []
        for entry in data:
            row = {field: entry.get(field) for field in ['header', 'title', 'titleUrl', 'time', 'description']}
            row['activity_controls'] = ', '.join(entry.get('activityControls', []))
            row['products'] = ', '.join(entry.get('products', []))
            details = entry.get('details', [])
            row['search_detail'] = details[0].get('name') if details else None
            subtitles = entry.get('subtitles', [])
            row['channel_name'] = subtitles[0].get('name') if subtitles else None
            row['channel_url'] = subtitles[0].get('url') if subtitles else None
            flattened.append(row)

        df = pd.DataFrame(flattened)
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'], errors='coerce')

        df.rename(columns={'titleUrl': 'title_url'}, inplace=True)
        return df

    @staticmethod
    def extract_video_id(url):
        if not url:
            return None
        match = re.search(r"v=([^&]+)", url)
        if match:
            return match.group(1)
        match_short = re.search(r"youtu\.be/([^?&]+)", url)
        if match_short:
            return match_short.group(1)
        return None
