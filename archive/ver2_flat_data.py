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
        if subtitles:
            row['channel_name'] = subtitles[0].get('name')
            row['channel_url'] = subtitles[0].get('url')
        
        flattened.append(row)
    
    df = pd.DataFrame(flattened)
    
    # Convert time to datetime
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
    
    return df

# Usage
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    
    watch_df = flatten_data(r"youtube_data\history\watch-history.json")
    search_df = flatten_data(r"youtube_data\history\search-history.json")
    
    print("=== Watch History Preview ===")
    print(watch_df.head())
    print(f"Shape: {watch_df.shape}")
    
    print("\n=== Search History Preview ===") 
    print(search_df.head())
    print(f"Shape: {search_df.shape}")