# SIBRA Unified Email & Indonesian Phone Scraper (v2.0)

A high-performance, asynchronous web scraper that extracts and validates **Emails** and **Indonesian Phone / WhatsApp Numbers** simultaneously in a **single crawl pass** (*sekali jalan*).

---

## 🌟 Key Features

1. **Single-Pass Extraction (Sekali Jalan)**:
   - Crawls each web page once and simultaneously extracts verified emails and phone numbers.
   - Saves 50%+ bandwidth and crawling time compared to running separate tools.
2. **Correlated Lead Generation**:
   - Matches and groups all contact information (Emails + Phone numbers) discovered per domain / URL.
3. **Advanced Email Validation**:
   - Strict anti-false-positive regex filtering out web assets (`.png`, `.js`, `.css`, etc.).
   - Blacklist filter for common placeholder and repository domains/emails.
   - De-obfuscation for protected emails (e.g. `user [at] company [dot] com` -> `user@company.com`).
4. **Indonesian Telecom & WhatsApp Validation**:
   - Recognizes Indonesian mobile operators: **Telkomsel** (Halo, SimPATI, AS, By.U), **Indosat Ooredoo** (IM3, Matrix, Mentari), **XL Axiata**, **Axis**, **Tri (3)**, and **Smartfren**.
   - Recognizes **PSTN Landlines** across Indonesian area codes (021 Jabodetabek, 022 Bandung, 031 Surabaya, 061 Medan, 0361 Bali, etc.).
   - Automatically generates international E.164 formatting (`+628...`) and direct **WhatsApp click-to-chat links** (`https://wa.me/628...`).
   - Extracts from HTML `<a>` tags (`tel:`, `wa.me/`, `api.whatsapp.com`), `data-*` attributes, and plain text.
5. **Search Engine Lead Gen (Bing, Yahoo, DuckDuckGo)**:
   - Enter keyword queries (e.g. *"digital marketing agency in jakarta"*, *"klinik kecantikan surabaya"*) to automatically discover and crawl lead websites.
6. **Modern Streamlit Dashboard (Dark & Light Theme)**:
   - Real-time live crawling logs and 5 live metrics.
   - Filterable & searchable interactive tables.
   - **Multi-Sheet Excel (`.xlsx`) Export** (Sheet 1: Combined Leads, Sheet 2: Emails, Sheet 3: Phone Numbers), individual CSVs, and JSON.
7. **Console CLI Support**:
   - Run directly in command line with interactive prompts or `--cli` flag.

---

## 🛠️ Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd e:\File_IRFAN\CODE\scraping\email-nomor
   ```

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 How to Run

### Option 1: Streamlit Web UI (Recommended)
Run the web dashboard directly:
```bash
streamlit run app.py
```
Pilih mode **Batch Company Target List (100 Focus Targets)** di sidebar untuk menjalankan scraping target 100 perusahaan secara visual.

### Option 2: Batch Target Scraper (CLI Mode)
Jalankan scraping otomatis untuk 100 target perusahaan:
```bash
python batch_scraper.py
```
*Atau via launcher:*
```bash
python scraper.py --batch
```
Hasil akan langsung disimpan bertahap ke `target_companies_leads.xlsx` dan `target_companies_leads.csv`.

### Option 3: Single URL / Keyword Console CLI Mode
Run in terminal mode:
```bash
python scraper.py --cli
```

---

## 📊 Output Formats

- **Multi-Sheet Excel (`.xlsx`)**:
  - `Combined Leads`: Full profile per source URL (Emails, Phone Numbers, Domain, Timestamp).
  - `Emails`: Validated Email list with Domain and Source URLs.
  - `Phone Numbers`: E.164, National Format, Operator / Carrier, Type, WhatsApp Link, and Source URLs.
- **CSV & JSON**: Instant downloads for individual datasets.

---

## ⚖️ License
MIT License
