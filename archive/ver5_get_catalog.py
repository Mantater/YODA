import json
import re
import pandas as pd
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from tqdm import tqdm  # progress bar

# ---------------------------
# STEP 1: Flatten history JSON
# ---------------------------
def flatten_data(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    flattened = []
    for entry in data:
        row = {}
        
        # Copy simple fields directly
        for field in ['header', 'title', 'titleUrl', 'time', 'description']:
            row[field] = entry.get(field)
        
        # Handle arrays
        row['activityControls'] = ', '.join(entry.get('activityControls', []))
        row['products'] = ', '.join(entry.get('products', []))
        
        # Extract first detail name if exists
        details = entry.get('details', [])
        row['search_detail'] = details[0].get('name') if details else None
        
        # Extract subtitle info
        subtitles = entry.get('subtitles', [])
        row['channel_name'] = subtitles[0].get('name') if subtitles else None
        row['channel_url'] = subtitles[0].get('url') if subtitles else None
        
        flattened.append(row)
    
    df = pd.DataFrame(flattened)
    
    # Convert time to datetime
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
    
    # Rename columns to snake_case
    df.rename(columns={
        'titleUrl': 'title_url',
        'activityControls': 'activity_controls'
    }, inplace=True)
    
    return df

# ---------------------------
# STEP 2: Extract video IDs
# ---------------------------
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

# ---------------------------
# STEP 3: YouTube API Helpers
# ---------------------------
def get_category_mapping(youtube, region="US"):
    response = youtube.videoCategories().list(
        part="snippet",
        regionCode=region
    ).execute()
    return {item["id"]: item["snippet"]["title"] for item in response["items"]}

def fetch_video_metadata(youtube, video_ids):
    try:
        response = youtube.videos().list(
            part="snippet",
            id=",".join(video_ids)
        ).execute()
    except Exception as e:
        print(f"API Error: {e}")
        return []

    results = []
    for item in response.get("items", []):
        vid = item["id"]
        snippet = item.get("snippet", {})
        results.append((
            vid,
            snippet.get("categoryId"),
            snippet.get("title"),
            snippet.get("description")
        ))
    return results

def enrich_vid_meta(df, youtube, category_map):
    all_results = []
    video_ids = df["video_id"].dropna().unique().tolist()
    
    for i in tqdm(range(0, len(video_ids), 50), desc="Fetching video metadata"):
        batch = video_ids[i:i+50]
        results = fetch_video_metadata(youtube, batch)
        all_results.extend(results)
    
    meta_df = pd.DataFrame(all_results, columns=["video_id", "category_id", "video_title", "video_description"])
    meta_df["category_name"] = meta_df["category_id"].map(category_map)
    
    return df.merge(meta_df, on="video_id", how="left")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    
    # Load API key
    load_dotenv(dotenv_path=r"api_keys/YT_API_KEY.env")
    API_KEY = os.getenv("YT_API_KEY")
    youtube = build("youtube", "v3", developerKey=API_KEY)
    
    # --- Watch History ---
    watch_df = flatten_data(r"youtube_data\history\watch-history.json")
    watch_df_clean = watch_df[
        ~(watch_df['channel_name'].isna() | watch_df['search_detail'].eq("From Google Ads"))
    ].copy()
    watch_df_clean["video_id"] = watch_df_clean["title_url"].apply(extract_video_id)
    
    # Enrich watch history with YouTube metadata
    category_map = get_category_mapping(youtube)
    watch_enriched_df = enrich_vid_meta(watch_df_clean, youtube, category_map)
    
    # Replace title with cleaned video_title from API
    watch_enriched_df['title'] = watch_enriched_df['video_title']
    
    # Drop unnecessary columns
    watch_cols_to_drop = [
        'header', 'description', 'activity_controls', 'products',
        'search_detail', 'title_url', 'channel_url', 'video_title'
    ]
    watch_enriched_df.drop(columns=[c for c in watch_cols_to_drop if c in watch_enriched_df.columns], inplace=True)
    
    # --- Search History ---
    search_df = flatten_data(r"youtube_data\history\search-history.json")

    # Remove "Searched for " prefix from titles
    search_df['title'] = search_df['title'].str.replace(r'^Searched for ', '', regex=True)

    # Remove ads safely
    search_df_clean = search_df[
        ~((search_df['search_detail'] == "From Google Ads") & (search_df['description'].notna()))
    ].copy()

    # Extract video_id where available (optional, mostly None)
    search_df_clean["video_id"] = search_df_clean["title_url"].apply(extract_video_id)

    # Add placeholder for future category classification
    search_df_clean['category_guess'] = None

    # Drop unnecessary columns
    search_cols_to_drop = [
        'header', 'title_url', 'description', 'activity_controls',
        'products', 'search_detail', 'channel_name', 'channel_url'
    ]
    search_df_final = search_df_clean.drop(columns=[c for c in search_cols_to_drop if c in search_df_clean.columns])

    # Optional: flag video vs plain text searches
    search_df_final['is_video'] = search_df_final['video_id'].notna()

    # Preview
    print("=== Search History Cleaned ===")
    print(search_df_final.head())
    print(f"Shape: {search_df_clean.shape} → {search_df_final.shape}")
