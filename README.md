# SIBRA Unified Email and Indonesian Phone Scraper (v2.0)

An asynchronous web scraping engine that extracts and validates email addresses and Indonesian telephone or WhatsApp numbers concurrently in a single crawl pass.

---

## Key Features

1. **Single-Pass Concurrent Extraction**:
   - Crawls target pages once to extract validated email addresses and telephone numbers simultaneously.
   - Reduces network bandwidth consumption and crawl time.
2. **Correlated Lead Generation**:
   - Aggregates and links all discovered contact records (emails, mobile numbers, and landlines) to their source domain and page URL.
3. **Email Validation Engine**:
   - Applies strict anti-false-positive filtering to exclude static web asset extensions (`.png`, `.js`, `.css`, `.svg`).
   - Filters blacklisted domains, placeholder addresses, and generic service emails.
   - De-obfuscates masked email formats (for example, `user [at] company [dot] com` into `user@company.com`).
4. **Indonesian Telecom and WhatsApp Parsing**:
   - Identifies major Indonesian mobile operators including Telkomsel (Halo, SimPATI, AS, By.U), Indosat Ooredoo (IM3, Matrix, Mentari), XL Axiata, Axis, Tri (3), and Smartfren.
   - Identifies Indonesian PSTN landline area codes (such as 021 Jabodetabek, 022 Bandung, 031 Surabaya, 061 Medan, and 0361 Bali).
   - Generates international standard E.164 formats (`+628...`) and direct WhatsApp click-to-chat links (`https://wa.me/628...`).
   - Parses contact data from HTML anchors (`tel:`, `wa.me/`, `api.whatsapp.com`), `data-*` attributes, and raw document text.
5. **Search Engine Discovery (Bing, Yahoo, DuckDuckGo)**:
   - Queries search engines using industry keywords to automatically identify and crawl candidate business websites.
6. **Streamlit Web Dashboard**:
   - Displays real-time crawling logs and session metrics.
   - Provides searchable, filterable data tables with theme support.
   - Exports data to multi-sheet Microsoft Excel (`.xlsx`), CSV, and JSON files.
7. **Command Line Interface (CLI)**:
   - Supports batch operations and interactive single-target execution via terminal commands.

---

## Installation

1. **Clone the repository and navigate to the directory**:
   ```bash
   git clone https://github.com/Irfan3006/email-number-scraping.git
   cd email-number-scraping
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Execution Modes

### 1. Streamlit Web Dashboard
Launch the interactive web application:
```bash
streamlit run app.py
```

### 2. Batch Company Target Scraper (CLI)
Execute automated discovery and contact extraction for company targets listed in `targets.txt`:
```bash
python batch_scraper.py
```
Alternatively, launch via the main CLI runner:
```bash
python scraper.py --batch
```
Results are incrementally exported to `target_companies_leads.xlsx` and `target_companies_leads.csv`.

### 3. Single URL or Keyword Search (CLI)
Run the interactive console scraper:
```bash
python scraper.py --cli
```

---

## Output Formats

- **Multi-Sheet Excel (`.xlsx`)**:
  - `Combined Leads`: Consolidated contact profiles grouped by source URL (Emails, Phone Numbers, Domain, Timestamp).
  - `Emails`: Validated email addresses, domain breakdown, and source URLs.
  - `Phone Numbers`: Phone records with E.164, National Format, Operator, Type, WhatsApp Links, and source URLs.
- **CSV and JSON**: Structured single-dataset exports for external database ingestion or spreadsheet analysis.

---

## License
MIT License
