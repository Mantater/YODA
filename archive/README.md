# YODA – YouTube Data Analysis Dashboard

YODA is a desktop application that allows users to upload YouTube watch/search history data and visualize it through an interactive analytics dashboard.

It provides insights such as:
- Watch history trends
- Search behavior analysis
- Channel and category distribution
- Time-based viewing patterns

---

# 🚀 Features

### 📤 Data Upload
- Upload YouTube watch-history JSON
- Upload search-history JSON
- Validates file selection before processing

### ⚙️ Data Processing
- Cleans and normalizes raw YouTube data
- Extracts video metadata
- Enriches data using YouTube Data API

### 📊 Dashboard Analytics
- Top channels watched
- Search history analysis
- Category distribution
- Daily / weekly viewing trends
- Correlation between search and watch behavior

### 📈 UX Improvements
- Progress bar during processing
- Disabled upload button until valid input
- Instant dashboard refresh after upload

---

# 🧠 Project Structure

```text
YODA/
│
├── app/
│   ├── ui/              # PyQt UI (main window, dashboard, upload)
│   ├── api/             # YouTube API integration
│   ├── core/            # Data processing + database logic
│
├── main.py              # Entry point (recommended)
└── README.md