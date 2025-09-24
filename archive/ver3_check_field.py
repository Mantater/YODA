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

def inspect_flattened_df(df, n_samples=3):
    """
    Inspect the columns of a flattened DataFrame.
    
    Parameters:
        df (pd.DataFrame): The DataFrame to inspect
        n_samples (int): Number of sample values to show per column
    """
    print(f"Total columns: {len(df.columns)}\n")
    
    for col in df.columns:
        print(f"Column: {col}")
        print(f" - Non-null count: {df[col].notna().sum()} / {len(df)}")
        # Show sample unique values (up to n_samples)
        sample_vals = df[col].dropna().unique()[:n_samples]
        print(f" - Sample values: {sample_vals}\n")

if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    
    # Watch history
    watch_df = flatten_data(r"youtube_data\history\watch-history.json")
    # Search history
    search_df = flatten_data(r"youtube_data\history\search-history.json")

    # Inspect watch history
    inspect_flattened_df(watch_df)
    # Inspect search history
    inspect_flattened_df(search_df)