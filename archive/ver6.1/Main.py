import pandas as pd
from Config import API_KEY, DB_NAME
from DataProcessing import DataProcessing
from YT_api import YouTubeAPI
from Database import Database

if __name__ == "__main__":
    pd.set_option("display.max_columns", None)

    # --- Watch History ---
    watch_processor = DataProcessing("youtube_data/history/watch-history.json")
    watch_df = watch_processor.flatten_data()
    watch_df_clean = watch_df[~(watch_df['channel_name'].isna() | watch_df['search_detail'].eq("From Google Ads"))].copy()
    watch_df_clean["video_id"] = watch_df_clean["title_url"].apply(DataProcessing.extract_video_id)

    # Enrich watch history
    yt_api = YouTubeAPI(API_KEY)
    category_map = yt_api.get_category_mapping()
    watch_enriched_df = yt_api.enrich_vid_meta(watch_df_clean, category_map)
    watch_enriched_df['title'] = watch_enriched_df['video_title']

    watch_cols_to_drop = ['header', 'description', 'activity_controls', 'products', 
                          'search_detail', 'title_url', 'channel_url', 'video_title']
    watch_enriched_df.drop(columns=[c for c in watch_cols_to_drop if c in watch_enriched_df.columns], inplace=True)

    # --- Search History ---
    search_processor = DataProcessing("youtube_data/history/search-history.json")
    search_df = search_processor.flatten_data()
    search_df['title'] = search_df['title'].str.replace(r'^Searched for ', '', regex=True)
    search_df_clean = search_df[~((search_df['search_detail'] == "From Google Ads") & (search_df['description'].notna()))].copy()
    search_df_clean["video_id"] = search_df_clean["title_url"].apply(DataProcessing.extract_video_id)
    search_df_clean['category_guess'] = None
    search_df_clean['is_video'] = search_df_clean['video_id'].notna()

    search_cols_to_drop = ['header', 'title_url', 'description', 'activity_controls', 
                           'products', 'search_detail', 'channel_name', 'channel_url',
                           'video_id', 'is_video']
    search_df_final = search_df_clean.drop(columns=[c for c in search_cols_to_drop if c in search_df_clean.columns])

    # Preview
    print("=== Watch History Cleaned & Enriched ===")
    print(watch_enriched_df.head())
    print("=== Search History Cleaned ===")
    print(search_df_final.head())

    # Save to SQLite
    db_handler = Database(DB_NAME)
    db_handler.save_to_database(watch_enriched_df, search_df_final)
