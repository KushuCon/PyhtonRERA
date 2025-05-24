# RERA Odisha Project Scraper

Python web scraper that extracts project information from the Odisha RERA website.

## Installation

1. **Install Python packages:**
```bash
pip install requests beautifulsoup4 selenium pandas
```

2. **Install ChromeDriver:**
   - Download from: https://chromedriver.chromium.org/
   - Match your Chrome browser version
   - Add to system PATH or project folder

## Usage

```bash
python rera_scraper.py
```

**Output:** 
- `scraped.json` - JSON format
- `rera_projects.csv` - CSV format

## Data Extracted

- RERA Registration Number
- Project Name  
- Promoter Name
- Promoter Address
- GST Number

## Requirements

- Python 3.7+
- Google Chrome browser
- Internet connection

## Dependencies

```
requests>=2.28.0
beautifulsoup4>=4.11.0
selenium>=4.15.0
pandas>=1.5.0
```

**Note:** Scrapes up to 6 projects per run. Website structure changes may require code updates.
