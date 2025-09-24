import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from Dashboard import DashboardWidget
from Uploads import UploadWidget

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube History Analyzer")
        self.setGeometry(200, 200, 1200, 800)

        # Tab widget instead of stacked widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Add tabs
        self.dashboard_page = DashboardWidget()
        self.upload_page = UploadWidget()

        self.tabs.addTab(self.dashboard_page, "Dashboard")
        self.tabs.addTab(self.upload_page, "Uploads")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainApp()
    main_win.show()
    sys.exit(app.exec())
