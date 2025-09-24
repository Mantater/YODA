from googleapiclient.discovery import build
from tqdm import tqdm
import pandas as pd

class YouTubeAPI:
    def __init__(self, api_key):
        self.youtube = build("youtube", "v3", developerKey=api_key)

    def get_category_mapping(self, region="US"):
        response = self.youtube.videoCategories().list(part="snippet", regionCode=region).execute()
        return {item["id"]: item["snippet"]["title"] for item in response["items"]}

    def fetch_video_metadata(self, video_ids):
        try:
            response = self.youtube.videos().list(part="snippet", id=",".join(video_ids)).execute()
        except Exception as e:
            print(f"API Error: {e}")
            return []
        results = []
        for item in response.get("items", []):
            vid = item["id"]
            snippet = item.get("snippet", {})
            results.append((vid, snippet.get("categoryId"), snippet.get("title"), snippet.get("description")))
        return results

    def enrich_vid_meta(self, df, category_map):
        all_results = []
        video_ids = df["video_id"].dropna().unique().tolist()
        for i in tqdm(range(0, len(video_ids), 50), desc="Fetching video metadata"):
            batch = video_ids[i:i+50]
            all_results.extend(self.fetch_video_metadata(batch))
        meta_df = pd.DataFrame(all_results, columns=["video_id", "category_id", "video_title", "video_description"])
        meta_df["category_name"] = meta_df["category_id"].map(category_map)
        return df.merge(meta_df, on="video_id", how="left")
