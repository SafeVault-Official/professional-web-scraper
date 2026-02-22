# professional-web-scraper

A robust, configurable web scraper built with Python. Supports CSV/JSON output and features a built-in retry mechanism.

## Features
- Robust HTTP requests with configurable retry strategy
- Configurable CSS selectors for broad website compatibility
- CSV and JSON output support
- Clean logging and clear English error messages
- Command-line interface for easy automation

## Requirements
Install dependencies:

```bash
pip install requests beautifulsoup4
```

## Usage
Run from the repository root:

```bash
python business_scraper.py "https://example.com/business-directory" \
  --card-selector "div.business-card" \
  --name-selector "h2" \
  --email-selector "span.email" \
  --format csv \
  --output marketing_list.csv
```

For JSON output:

```bash
python business_scraper.py "https://example.com/business-directory" --format json --output marketing_list.json
```
