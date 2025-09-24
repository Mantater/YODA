from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QGroupBox, QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import os
from DataProcessing import DataProcessing
from YT_api import YouTubeAPI
from Database import Database
from Config import API_KEY, DB_NAME

class UploadWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.watch_file = None
        self.search_file = None

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        # --- Title ---
        title = QLabel("Upload")
        title_font = QFont("Arial", 26)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # --- Watch Upload Section ---
        watch_group = QGroupBox("Upload Watch History")
        watch_font = QFont("Arial", 14)
        watch_group.setFont(watch_font)
        watch_layout = QHBoxLayout()
        self.watch_label = QLabel("No file selected")
        btn_watch = QPushButton("Choose File")
        btn_watch.clicked.connect(self.select_watch_file)
        watch_layout.addWidget(self.watch_label)
        watch_layout.addWidget(btn_watch)
        watch_group.setLayout(watch_layout)
        main_layout.addWidget(watch_group)

        # --- Search Upload Section ---
        search_group = QGroupBox("Upload Search History")
        search_group.setFont(watch_font)
        search_layout = QHBoxLayout()
        self.search_label = QLabel("No file selected")
        btn_search = QPushButton("Choose File")
        btn_search.clicked.connect(self.select_search_file)
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(btn_search)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # --- Process & Save Button ---
        self.btn_upload_data = QPushButton("Upload Data")
        self.btn_upload_data.setEnabled(False)
        self.btn_upload_data.setFixedWidth(200)
        self.btn_upload_data.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.btn_upload_data.clicked.connect(self.process_and_save)
        main_layout.addWidget(self.btn_upload_data, alignment=Qt.AlignmentFlag.AlignHCenter)

    # --- File Selection ---
    def select_watch_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select watch-history.json", "", "JSON Files (*.json)"
        )
        if file_path:
            self.watch_file = file_path
            self.watch_label.setText(os.path.basename(file_path))
            self.check_ready()

    def select_search_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select search-history.json", "", "JSON Files (*.json)"
        )
        if file_path:
            self.search_file = file_path
            self.search_label.setText(os.path.basename(file_path))
            self.check_ready()

    def check_ready(self):
        """Enable upload button only if both files are selected"""
        if self.watch_file and self.search_file:
            self.btn_upload_data.setEnabled(True)
        else:
            self.btn_upload_data.setEnabled(False)

    # --- Processing on button click ---
    def process_and_save(self):
        if not (self.watch_file and self.search_file):
            QMessageBox.warning(self, "Missing Files", "Please select both Watch and Search history files first.")
            return

        # Process Watch History
        processor_watch = DataProcessing(self.watch_file)
        watch_df = processor_watch.flatten_data()
        watch_df_clean = watch_df[~(watch_df['channel_name'].isna() | watch_df['search_detail'].eq("From Google Ads"))].copy()
        watch_df_clean["video_id"] = watch_df_clean["title_url"].apply(DataProcessing.extract_video_id)

        # Process Search History
        processor_search = DataProcessing(self.search_file)
        search_df = processor_search.flatten_data()
        search_df['title'] = search_df['title'].str.replace(r'^Searched for ', '', regex=True)
        search_df_clean = search_df[~((search_df['search_detail'] == "From Google Ads") & (search_df['description'].notna()))].copy()
        search_df_clean["video_id"] = search_df_clean["title_url"].apply(DataProcessing.extract_video_id)
        search_df_clean['category_guess'] = None
        search_df_clean['is_video'] = search_df_clean['video_id'].notna()
        search_cols_to_drop = ['header', 'title_url', 'description', 'activity_controls',
                               'products', 'search_detail', 'channel_name', 'channel_url',
                               'video_id', 'is_video']
        search_df_final = search_df_clean.drop(columns=[c for c in search_cols_to_drop if c in search_df_clean.columns])

        # Enrich Watch History with YouTube API
        yt_api = YouTubeAPI(API_KEY)
        category_map = yt_api.get_category_mapping()
        watch_enriched = yt_api.enrich_vid_meta(watch_df_clean, category_map)
        watch_enriched['title'] = watch_enriched['video_title']
        watch_cols_to_drop = ['header', 'description', 'activity_controls', 'products',
                              'search_detail', 'title_url', 'channel_url', 'video_title']
        watch_enriched.drop(columns=[c for c in watch_cols_to_drop if c in watch_enriched.columns], inplace=True)

        # Save to Database
        db_handler = Database(DB_NAME)
        db_handler.save_to_database(watch_enriched, search_df_final)

        QMessageBox.information(self, "Success", f"Data processed and saved to {DB_NAME}")
