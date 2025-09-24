import json
import pandas as pd

# --------------------
# Print fields from JSON files
# --------------------
def extract_all_fields_from_file(json_file):
    """
    Recursively extracts all field paths (including nested fields) from a JSON file.
    Returns a sorted list of unique fields.
    """
    def extract_all_fields(obj, prefix=""):
        fields = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                full_key = f"{prefix}{k}" if prefix == "" else f"{prefix}.{k}"
                fields.add(full_key)
                fields.update(extract_all_fields(v, full_key))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                full_key = f"{prefix}[{i}]"
                fields.update(extract_all_fields(item, full_key))
        return fields

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_fields = set()
    for entry in data:
        all_fields.update(extract_all_fields(entry))

    return sorted(all_fields)

# Example usage for watch history
watch_fields = extract_all_fields_from_file(r"youtube_data\history\watch-history.json")
print("Watch history fields:")
for field in watch_fields:
    print(field)

# Example usage for search history
search_fields = extract_all_fields_from_file(r"youtube_data\history\search-history.json")
print("\nSearch history fields:")
for field in search_fields:
    print(field)

print()

# --------------------
# Simple extraction without flattening
# --------------------
pd.set_option("display.max_columns", None)

def extract_history(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return pd.json_normalize(data, sep='.')

watch_df = extract_history(r"youtube_data\history\watch-history.json")
search_df = extract_history(r"youtube_data\history\search-history.json")

print(watch_df)
print(search_df)
print(f"Watch history shape: {watch_df.shape}")
print(f"Search history shape: {search_df.shape}")
print(f"Watch history columns: {list(watch_df.columns)}")
print(f"Search history columns: {list(search_df.columns)}")