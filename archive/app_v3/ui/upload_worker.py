from PyQt6.QtCore import QThread, pyqtSignal
from app.core.data_processing import DataProcessing
from app.api.yt_api import YouTubeAPI
from app.core.database import Database
from app.config import API_KEY

class UploadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, watch_file, search_file):
        super().__init__()
        self.watch_file = watch_file
        self.search_file = search_file

    def run(self):
        try:
            # --- STEP 1: Load watch ---
            processor_watch = DataProcessing(self.watch_file)
            watch_df = processor_watch.flatten_data()

            watch_df_clean = watch_df[
                ~(watch_df['channel_name'].isna() | watch_df['search_detail'].eq("From Google Ads"))
            ].copy()
            watch_df_clean["video_id"] = watch_df_clean["title_url"].apply(DataProcessing.extract_video_id)

            # --- STEP 2: Load search ---
            processor_search = DataProcessing(self.search_file)
            search_df = processor_search.flatten_data()

            search_df['title'] = search_df['title'].str.replace(r'^Searched for ', '', regex=True)

            search_df_clean = search_df[
                ~((search_df['search_detail'] == "From Google Ads") & (search_df['description'].notna()))
            ].copy()

            self.progress.emit(20)

            # --- STEP 3: API enrichment ---
            yt_api = YouTubeAPI(API_KEY)
            category_map = yt_api.get_category_mapping()

            watch_enriched = yt_api.enrich_vid_meta(
                watch_df_clean,
                category_map,
                progress_callback=lambda p: self.progress.emit(20 + int(p * 0.7))
            )

            # --- STEP 4: Save ---
            db_handler = Database()
            db_handler.save_to_database(watch_enriched, search_df_clean)
            self.progress.emit(100)

        except Exception as e:
            print("Upload error:", e)

        self.finished.emit()