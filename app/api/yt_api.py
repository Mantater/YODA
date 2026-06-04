from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
from tqdm import tqdm
import pandas as pd

class YouTubeAPI:
    def __init__(self, api_key):
        print(api_key)
        self.youtube = build(
            "youtube", 
            "v3", 
            developerKey=api_key
        )

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

    def enrich_vid_meta(self, df, category_map, progress_callback=None):
        all_results = []

        video_ids = df["video_id"].dropna().unique().tolist()
        total_batches = (len(video_ids) + 49) // 50

        for i, start in enumerate(range(0, len(video_ids), 50)):
            batch = video_ids[start:start + 50]

            # API call
            all_results.extend(self.fetch_video_metadata(batch))

            # progress update
            if progress_callback:
                percent = int((i + 1) / total_batches * 100)
                progress_callback(percent)

        # After loop
        meta_df = pd.DataFrame(
            all_results,
            columns=["video_id", "category_id", "video_title", "video_description"]
        )

        meta_df["category_name"] = meta_df["category_id"].map(category_map)

        return df.merge(meta_df, on="video_id", how="left")