import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QGroupBox, QMessageBox, QSizePolicy, QProgressDialog
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal
from app.ui.upload_worker import UploadWorker

class UploadWidget(QWidget):
    upload_done = pyqtSignal()
    
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

        # --- Info Message ---
        info_label = QLabel("Only .json files are accepted for upload.")
        info_font = QFont("Arial", 12)
        info_label.setFont(info_font)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

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
            QMessageBox.warning(self, "Missing Files", "Please select both files.")
            return

        self.worker = UploadWorker(self.watch_file, self.search_file)

        # Progress popup
        self.progress_dialog = QProgressDialog("Uploading data...", None, 0, 100, self)
        self.progress_dialog.setWindowTitle("Uploading")
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setCancelButton(None)
        self.progress_dialog.show()

        self.worker.progress.connect(self.progress_dialog.setValue)
        self.worker.finished.connect(self.upload_complete)

        self.worker.start()

    def upload_complete(self):
        self.progress_dialog.close()
        QMessageBox.information(self, "Upload Complete", "Data has been uploaded successfully.")
        self.upload_done.emit()