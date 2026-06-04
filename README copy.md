# YODA - YouTube Ordinary Data Analyzer

## Description
YODA is a desktop application that analyzes YouTube watch and search history. It provides insights into viewing habits, trends, and category preferences through interactive visualizations.

The app uses:
- PyQt6 (desktop UI)
- Dash + Plotly (data visualization)
- SQLite (local database)

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/Mantater/YODA.git
cd YODA
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Set up API key
Create a file:
```bash
app/config.py
```
or .env (depending on your implementation), and add:
```bash
YT_API_KEY=your_youtube_api_key_here
```
4. Run the application
```bash
python -m app.ui.main
```

## Usage
1. Launch the app
2. Upload:
    - watch-history.json
    - search-history.json
3. Click Upload Data
4. Explore dashboard analytics:
    - Top channels
    - Search trends
    -Category distribution
    Weekly/daily activity
    Correlations between search & watch behavior

## Features
- Upload and process YouTube history data
- Automatic enrichment via YouTube Data API
- Interactive dashboard with filters
- Visual analytics (bar, pie, line, scatter charts)
- SQLite database storage
- Real-time upload progress tracking

## Data Source (YouTube Takeout)
1. Go to Google Takeout
2. Select “YouTube and YouTube Music”
3. Choose “History”
4. Export as JSON

## Notes
- Run all commands from the project root (`YODA/`)
- Do NOT run files directly inside `app/ui`
- Archived versions are stored in `/archive` for reference only

## License
This project is licensed under the MIT License. See `LICENSE` for details.