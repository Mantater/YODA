import json
import pandas as pd

# --------------------
# Flatten data
# --------------------
def flatten_data(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    flattened = []
    for entry in data:
        row = {}
        
        # Copy simple fields directly
        for field in ['header', 'title', 'titleUrl', 'time', 'description']:
            row[field] = entry.get(field)
        
        # Handle arrays (join strings, take first dict)
        row['activityControls'] = ', '.join(entry.get('activityControls', []))
        row['products'] = ', '.join(entry.get('products', []))
        
        # Extract first detail name if exists
        details = entry.get('details', [])
        row['search_detail'] = details[0].get('name') if details else None
        
        # Extract subtitle info (for watch history)
        subtitles = entry.get('subtitles', [])
        row['channel_name'] = subtitles[0].get('name') if subtitles else None
        row['channel_url'] = subtitles[0].get('url') if subtitles else None
        
        flattened.append(row)
    
    df = pd.DataFrame(flattened)
    
    # Convert time to datetime
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
    
    return df

# --------------------
# Main execution
# --------------------
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    
    # Watch history
    watch_df = flatten_data(r"youtube_data\history\watch-history.json")
    
    # Remove ads safely
    watch_df_clean = watch_df[
        ~(
            watch_df.get('channel_name', pd.Series([None]*len(watch_df))).isna() |
            (watch_df.get('search_detail', pd.Series([None]*len(watch_df))) == "From Google Ads")
        )
    ].copy()

    # Search history
    search_df = flatten_data(r"youtube_data\history\search-history.json")
    
    # Clean search_df titles by removing "Searched for " prefix
    search_df['title'] = search_df['title'].str.replace(r'^Searched for ', '', regex=True)

    # Remove ads safely
    search_df_clean = search_df[
        ~(
            (search_df.get('search_detail', pd.Series([None]*len(search_df))) == "From Google Ads") &
            (search_df.get('description', pd.Series([None]*len(search_df))).notna())
        )
    ].copy()

    # Preview
    print("=== Watch History Preview ===")
    print(watch_df_clean.head())
    print(f"Shape: {watch_df.shape} vs {watch_df_clean.shape}")
    
    print("\n=== Search History Preview ===")
    print(search_df_clean.head())
    print(f"Shape: {search_df.shape} vs {search_df_clean.shape}")
