"""SIBRA Unified Email & Phone Scraper - Streamlit Dashboard.

Interactive web UI providing real-time scraping controls, multi-tab results,
Excel/CSV/JSON export, and telco/domain performance analytics.
"""

import asyncio
import io
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from scraper_engine import (
    AsyncDualScraper,
    EmailValidator,
    PhoneNumberValidator,
    SearchEngineScraper,
)

st.set_page_config(
    page_title="SIBRA Unified Email & Phone Scraper Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load default 100 targets if available
DEFAULT_TARGETS = ""
if os.path.exists("targets.txt"):
    with open("targets.txt", "r", encoding="utf-8") as f:
        DEFAULT_TARGETS = f.read()

# Theme Selector in Sidebar
theme = st.sidebar.selectbox(
    "Theme Mode", ["Dark Mode", "Light Mode"], index=0
)

DARK_THEME_CSS = """
<style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0E1117 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1E1E24 !important;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    label,
    [data-testid="stMetricLabel"],
    [data-testid="stTab"] p {
        color: #FAFAFA !important;
    }
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    .main-title {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #FF3366, #FF6633, #FFCC33);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #88888B !important;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1E1E24;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #2E2E38;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        color: #FFFFFF !important;
    }
    .terminal-box {
        background-color: #0B0C10;
        color: #4AF626;
        font-family: 'Courier New', monospace;
        padding: 1rem;
        border-radius: 8px;
        height: 350px;
        overflow-y: scroll;
        border: 1px solid #1F2833;
        font-size: 0.85rem;
        white-space: pre-wrap;
    }
    .stTextArea textarea, .stTextInput input, .stNumberInput input {
        background-color: #161821 !important;
        color: #FAFAFA !important;
        border: 1px solid #3B3F54 !important;
    }
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #161821 !important;
        color: #FAFAFA !important;
        border-color: #3B3F54 !important;
    }
    div[role="listbox"] ul li {
        background-color: #161821 !important;
        color: #FAFAFA !important;
    }
    div[role="listbox"] ul li:hover {
        background-color: #2D313E !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #1E1E24 !important;
        color: #FAFAFA !important;
        border: 1px solid #3B3F54 !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #2D313E !important;
        border-color: #FF3366 !important;
        color: #FF3366 !important;
    }
    .stButton>button:disabled, .stDownloadButton>button:disabled {
        background-color: #161821 !important;
        color: #88888B !important;
        border-color: #2E2E38 !important;
    }
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #1E1E24 !important;
        border-radius: 8px;
        padding: 4px;
        border: 1px solid #2E2E38 !important;
        gap: 4px !important;
    }
    div[data-testid="stRadio"] label {
        background-color: transparent !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        margin-right: 0px !important;
        cursor: pointer !important;
        color: #FAFAFA !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #FF3366 !important;
        color: #FFFFFF !important;
    }
</style>
"""

LIGHT_THEME_CSS = """
<style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    label,
    [data-testid="stMetricLabel"],
    [data-testid="stTab"] p {
        color: #0F172A !important;
    }
    [data-testid="stMetricValue"] {
        color: #0F172A !important;
    }
    .main-title {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #FF3366, #FF6633, #FFCC33);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #475569 !important;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F1F5F9;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        color: #0F172A !important;
    }
    .terminal-box {
        background-color: #F8FAFC;
        color: #0F172A;
        font-family: 'Courier New', monospace;
        padding: 1rem;
        border-radius: 8px;
        height: 350px;
        overflow-y: scroll;
        border: 1px solid #CBD5E1;
        font-size: 0.85rem;
        white-space: pre-wrap;
    }
    .stTextArea textarea, .stTextInput input, .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
    }
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    div[role="listbox"] ul li {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
    }
    div[role="listbox"] ul li:hover {
        background-color: #F1F5F9 !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #F1F5F9 !important;
        border-color: #FF3366 !important;
        color: #FF3366 !important;
    }
    .stButton>button:disabled, .stDownloadButton>button:disabled {
        background-color: #F8FAFC !important;
        color: #94A3B8 !important;
        border-color: #E2E8F0 !important;
    }
    div[data-testid="stRadio"] > div {
        flex-direction: row !important;
        background-color: #F1F5F9 !important;
        border-radius: 8px;
        padding: 4px;
        border: 1px solid #E2E8F0 !important;
        gap: 4px !important;
    }
    div[data-testid="stRadio"] label {
        background-color: transparent !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        margin-right: 0px !important;
        cursor: pointer !important;
        color: #0F172A !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #FF3366 !important;
        color: #FFFFFF !important;
    }
</style>
"""

theme_css = DARK_THEME_CSS if theme == "Dark Mode" else LIGHT_THEME_CSS
st.markdown(theme_css, unsafe_allow_html=True)

# Session State Initialization
if "scraped_emails" not in st.session_state:
    st.session_state.scraped_emails = {}

if "scraped_numbers" not in st.session_state:
    st.session_state.scraped_numbers = {}

if "scraped_leads" not in st.session_state:
    st.session_state.scraped_leads = {}

if "scraped_companies" not in st.session_state:
    st.session_state.scraped_companies = []

if "logs" not in st.session_state:
    st.session_state.logs = []

if "stats" not in st.session_state:
    st.session_state.stats = {
        "crawled": 0,
        "success": 0,
        "errors": 0,
        "running": False,
    }

if "active_tab_index" not in st.session_state:
    st.session_state.active_tab_index = 0


def reset_session():
    """Clear scraped contacts, leads, metrics, and terminal logs."""
    st.session_state.scraped_emails = {}
    st.session_state.scraped_numbers = {}
    st.session_state.scraped_leads = {}
    st.session_state.scraped_companies = []
    st.session_state.logs = ["Session cleared and ready."]
    st.session_state.active_tab_index = 0
    st.session_state.stats = {
        "crawled": 0,
        "success": 0,
        "errors": 0,
        "running": False,
    }


# ================= SIDEBAR CONFIGURATION =================
st.sidebar.markdown("### ⚙️ SCRAPING TARGET & MODE")
scrape_target = st.sidebar.selectbox(
    "Target Extraction",
    [
        "Both Emails & Phone Numbers (Simultaneous)",
        "Emails Only",
        "Phone Numbers Only",
    ],
    help=(
        "Pilih target ekstraksi. Opsi simultan akan mengekstrak email "
        "dan nomor telepon sekaligus dalam 1 kali crawl per halaman."
    ),
)

crawl_mode = st.sidebar.selectbox(
    "Scraping Mode",
    [
        "Batch Company Target List (100 Focus Targets)",
        "Direct URLs",
        "Keyword Search Lead Gen",
    ],
    help=(
        "Pilih mode crawling: Batch Perusahaan Target, "
        "Daftar URL Langsung, atau Pencarian Kata Kunci."
    ),
)

st.sidebar.markdown("### 🚀 CRAWLER SETTINGS")
concurrency = st.sidebar.slider(
    "Concurrent Connections",
    min_value=1,
    max_value=50,
    value=15,
    help="Number of concurrent web page requests.",
)
max_pages = st.sidebar.number_input(
    "Max Pages to Crawl (Per Target / Total)",
    min_value=5,
    max_value=20000,
    value=15 if "Batch" in crawl_mode else 200,
    step=5,
    help="Stop crawling after visiting this many pages.",
)
max_depth = st.sidebar.slider(
    "Crawl Depth",
    min_value=0,
    max_value=5,
    value=1,
    help="Depth level to follow links (0=Start pages only).",
)
internal_only = st.sidebar.checkbox(
    "Internal Domain Only",
    value=True,
    help="Only crawl links within the starting website domains.",
)
deobfuscate = st.sidebar.checkbox(
    "De-obfuscate Emails & Numbers",
    value=True,
    help="Convert obfuscated email and phone patterns automatically.",
)

st.sidebar.markdown("### 📞 TELECOM & PHONE FILTERS")
include_landlines = st.sidebar.checkbox(
    "Include Landline / PSTN Numbers",
    value=True,
    help=(
        "Include fixed landline numbers (e.g. 021, 022, 031, 061, 024, etc.)."
    ),
)
allowed_operators_input = st.sidebar.multiselect(
    "Filter by Mobile Operators",
    [
        "Telkomsel (Halo)",
        "Telkomsel (SimPATI)",
        "Telkomsel (Loop/SimPATI)",
        "Telkomsel (Kartu AS)",
        "Telkomsel (By.U/AS)",
        "Indosat Ooredoo (IM3)",
        "Indosat Ooredoo (Matrix/Mentari)",
        "Indosat Ooredoo (Matrix)",
        "Indosat Ooredoo (Mentari)",
        "XL Axiata",
        "Axis",
        "Tri (3)",
        "Smartfren",
    ],
    default=[],
    help="Leave empty to scrape all operators.",
)

st.sidebar.markdown("### 🛡️ BLACKLIST & ANTI-FALSE-POSITIVE")
blacklist_domains_input = st.sidebar.text_area(
    "Blacklist Domains (comma separated)",
    value=(
        "sentry.io, fontawesome.com, bootstrap.com, "
        "w3.org, github.com, google.com"
    ),
    help="Ignore emails from these domains.",
)
blacklist_emails_input = st.sidebar.text_area(
    "Blacklist Emails (comma separated)",
    value="git@github.com, noreply@github.com",
    help="Ignore these specific email addresses.",
)
blacklist_numbers_input = st.sidebar.text_area(
    "Blacklist Phone Numbers (comma separated)",
    value="08123456789, 081234567890, 08111111111",
    help="Ignore these specific phone numbers.",
)

# Header Title
st.markdown(
    '<a href="https://sibra.store" target="_blank" '
    'style="text-decoration: none; color: inherit;">'
    '<div class="main-title">SIBRA UNIFIED EMAIL & PHONE SCRAPER</div></a>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">An aggressive, high-efficiency, multi-threaded OOP '
    "scraper with simultaneous Email & Indonesian WhatsApp/Phone extraction "
    "in a single pass.</div>",
    unsafe_allow_html=True,
)

# Main Navigation Tabs
NAV_OPTIONS = [
    "Live Dashboard",
    "Combined Leads Table",
    "Scraped Emails Table",
    "Scraped Numbers Table",
    "Performance Analytics",
]
active_tab = st.radio(
    "Navigation",
    NAV_OPTIONS,
    index=st.session_state.active_tab_index,
    horizontal=True,
    label_visibility="collapsed",
)
st.session_state.active_tab_index = NAV_OPTIONS.index(active_tab)

custom_domains = {
    d.strip().lower() for d in blacklist_domains_input.split(",") if d.strip()
}
custom_emails = {
    e.strip().lower() for e in blacklist_emails_input.split(",") if e.strip()
}
custom_blacklist_nums = {
    n.strip() for n in blacklist_numbers_input.split(",") if n.strip()
}

scrape_emails_flag = "Email" in scrape_target
scrape_phones_flag = "Phone" in scrape_target

# ================= TAB 1: LIVE DASHBOARD =================
if active_tab == "Live Dashboard":
    col_input, col_action = st.columns([3, 1])

    with col_input:
        if crawl_mode == "Batch Company Target List (100 Focus Targets)":
            target_input = st.text_area(
                "Company Target Names (one per line)",
                value=DEFAULT_TARGETS,
                height=160,
                help=(
                    "Daftar nama perusahaan target yang akan dicari "
                    "dan diekstrak kontaknya secara otomatis."
                ),
            )
        elif crawl_mode == "Direct URLs":
            target_input = st.text_area(
                "Target URLs (one per line)",
                value=(
                    "https://news.ycombinator.com/\nhttps://www.wikipedia.org/"
                ),
                height=120,
                help="Enter target website start URLs, e.g. https://domain.com",
            )
        else:
            target_input = st.text_input(
                "Search Keywords Lead Gen (e.g. 'marmer granit Jakarta')",
                value="supplier marmer dan kaca indonesia",
                help=(
                    "Type search terms to query Bing, Yahoo, and DuckDuckGo "
                    "for lead links."
                ),
            )
            search_num_results = st.number_input(
                "Max Search Result Links to Scrape",
                min_value=5,
                max_value=200,
                value=25,
                step=5,
            )

    with col_action:
        st.markdown("<br>", unsafe_allow_html=True)
        btn_start = st.button(
            "Start Dual Scraping",
            use_container_width=True,
            disabled=st.session_state.stats["running"],
        )
        btn_stop = st.button(
            "Stop Scraping",
            use_container_width=True,
            disabled=not st.session_state.stats["running"],
        )
        btn_clear = st.button(
            "Clear Results",
            use_container_width=True,
            on_click=reset_session,
            disabled=st.session_state.stats["running"],
        )

    if btn_stop:
        st.session_state.stats["running"] = False
        st.success(
            "Scraper stop requested. It will exit gracefully on next page."
        )

    # 5 Key Metrics
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        m_emails = st.metric(
            "Emails Found", len(st.session_state.scraped_emails)
        )
    with m_col2:
        m_numbers = st.metric(
            "Phone Numbers", len(st.session_state.scraped_numbers)
        )
    with m_col3:
        if st.session_state.scraped_companies:
            m_leads = st.metric(
                "Companies Scraped",
                f"{len(st.session_state.scraped_companies)}",
            )
        else:
            m_leads = st.metric(
                "Contacted Leads", len(st.session_state.scraped_leads)
            )
    with m_col4:
        m_pages = st.metric("Pages Visited", st.session_state.stats["crawled"])
    with m_col5:
        m_status = st.metric(
            "Reqs (OK / Err)",
            f"{st.session_state.stats['success']} / "
            f"{st.session_state.stats['errors']}",
        )

    st.markdown("### Real-time Scraping Log")
    log_area = st.empty()
    log_content = "\n".join(st.session_state.logs)
    log_area.markdown(
        f'<div class="terminal-box">{log_content}</div>',
        unsafe_allow_html=True,
    )

    if btn_start:
        st.session_state.stats["running"] = True
        st.session_state.logs = [
            "[INFO] Initiating SIBRA Unified Scraper engine..."
        ]
        st.session_state.scraped_emails = {}
        st.session_state.scraped_numbers = {}
        st.session_state.scraped_leads = {}
        st.session_state.scraped_companies = []
        st.session_state.stats["crawled"] = 0
        st.session_state.stats["success"] = 0
        st.session_state.stats["errors"] = 0

        email_val = EmailValidator(
            custom_blacklist_domains=custom_domains,
            custom_blacklist_emails=custom_emails,
        )
        phone_val = PhoneNumberValidator(
            custom_blacklist_numbers=custom_blacklist_nums,
            allowed_operators=(
                allowed_operators_input if allowed_operators_input else None
            ),
            include_landline=include_landlines,
        )

        def update_ui_log(msg):
            st.session_state.logs.append(msg)
            if len(st.session_state.logs) > 500:
                st.session_state.logs.pop(0)
            log_text = "\n".join(st.session_state.logs)
            log_area.markdown(
                f'<div class="terminal-box">{log_text}</div>',
                unsafe_allow_html=True,
            )

        if crawl_mode == "Batch Company Target List (100 Focus Targets)":
            companies = [
                c.strip()
                for c in target_input.split("\n")
                if c.strip() and not c.strip().startswith("#")
            ]
            unique_companies = list(dict.fromkeys(companies))

            if not unique_companies:
                st.error("No valid company targets provided.")
                st.session_state.stats["running"] = False
            else:
                update_ui_log(
                    f"[BATCH] Starting automated batch scrape for "
                    f"{len(unique_companies)} target companies..."
                )
                searcher = SearchEngineScraper()

                async def run_batch_pipeline():
                    for idx, comp in enumerate(unique_companies, 1):
                        if not st.session_state.stats["running"]:
                            update_ui_log("[INFO] Batch stopped by user.")
                            break

                        update_ui_log(
                            f"[{idx}/{len(unique_companies)}] [SEARCH] "
                            f"Finding verified website for: '{comp}'..."
                        )
                        search_urls = []
                        try:
                            search_urls = await searcher.search_company(comp)
                        except Exception as e:
                            update_ui_log(
                                f"[WARN] Search error for {comp}: {e}"
                            )

                        if not search_urls:
                            update_ui_log(
                                f"  [-] No verified company website "
                                f"found for '{comp}'."
                            )
                            st.session_state.scraped_companies.append(
                                {
                                    "Company Target": comp,
                                    "Status": "Website Not Found",
                                    "Discovered Website": "-",
                                    "Emails": "-",
                                    "Phone Numbers": "-",
                                    "WhatsApp Links": "-",
                                    "Carriers / Types": "-",
                                    "Total Emails": 0,
                                    "Total Phones": 0,
                                    "Scraped Pages": 0,
                                    "Source URLs": "-",
                                }
                            )
                            continue

                        update_ui_log(
                            f"  [+] Target verified: {search_urls[0]} | "
                            "Crawling contact pages..."
                        )

                        def batch_callback(msg, scraper_inst):
                            if not st.session_state.stats["running"]:
                                scraper_inst.is_running = False
                            st.session_state.stats["crawled"] += 1
                            if "[SUCCESS]" in msg:
                                st.session_state.stats["success"] += 1
                            elif "[ERROR]" in msg or "[WARN]" in msg:
                                st.session_state.stats["errors"] += 1
                            update_ui_log(msg)

                        sub_scraper = AsyncDualScraper(
                            start_urls=search_urls[:2],
                            max_depth=max_depth,
                            max_pages=max_pages,
                            concurrent_connections=concurrency,
                            internal_only=internal_only,
                            deobfuscate=deobfuscate,
                            scrape_emails=scrape_emails_flag,
                            scrape_phones=scrape_phones_flag,
                            email_validator=email_val,
                            phone_validator=phone_val,
                            update_callback=batch_callback,
                        )

                        try:
                            await sub_scraper.start()
                        except Exception as e:
                            update_ui_log(
                                f"[ERROR] Error crawling {comp}: {e}"
                            )

                        # Aggregate results
                        c_emails = sorted(
                            list(sub_scraper.scraped_emails.keys())
                        )
                        c_phones = sorted(
                            [
                                p["e164"]
                                for p in sub_scraper.scraped_numbers.values()
                            ]
                        )
                        c_was = sorted(
                            [
                                p["wa_link"]
                                for p in sub_scraper.scraped_numbers.values()
                                if p.get("wa_link") and p["wa_link"] != "-"
                            ]
                        )
                        c_ops = sorted(
                            list(
                                {
                                    f"{p['operator']} ({p['type']})"
                                    for p in (
                                        sub_scraper.scraped_numbers.values()
                                    )
                                }
                            )
                        )

                        for em, s_urls in sub_scraper.scraped_emails.items():
                            if em not in st.session_state.scraped_emails:
                                st.session_state.scraped_emails[em] = set()
                            st.session_state.scraped_emails[em].update(s_urls)

                        for (
                            e164,
                            pdata,
                        ) in sub_scraper.scraped_numbers.items():
                            if e164 not in st.session_state.scraped_numbers:
                                st.session_state.scraped_numbers[e164] = pdata
                            else:
                                st.session_state.scraped_numbers[e164][
                                    "sources"
                                ].update(pdata["sources"])

                        status_comp = (
                            "Success (Data Found)"
                            if (c_emails or c_phones)
                            else "Scraped (No Contacts Found)"
                        )
                        st.session_state.scraped_companies.append(
                            {
                                "Company Target": comp,
                                "Status": status_comp,
                                "Discovered Website": (
                                    search_urls[0] if search_urls else "-"
                                ),
                                "Emails": (
                                    ", ".join(c_emails) if c_emails else "-"
                                ),
                                "Phone Numbers": (
                                    ", ".join(c_phones) if c_phones else "-"
                                ),
                                "WhatsApp Links": (
                                    ", ".join(c_was) if c_was else "-"
                                ),
                                "Carriers / Types": (
                                    ", ".join(c_ops) if c_ops else "-"
                                ),
                                "Total Emails": len(c_emails),
                                "Total Phones": len(c_phones),
                                "Scraped Pages": sub_scraper.crawled_count,
                                "Source URLs": ", ".join(
                                    list(sub_scraper.visited_urls)[:3]
                                ),
                            }
                        )

                        m_emails.metric(
                            "Emails Found",
                            len(st.session_state.scraped_emails),
                        )
                        m_numbers.metric(
                            "Phone Numbers",
                            len(st.session_state.scraped_numbers),
                        )
                        m_leads.metric(
                            "Companies Scraped",
                            f"{len(st.session_state.scraped_companies)} / "
                            f"{len(unique_companies)}",
                        )
                        m_pages.metric(
                            "Pages Visited",
                            st.session_state.stats["crawled"],
                        )
                        m_status.metric(
                            "Reqs (OK / Err)",
                            f"{st.session_state.stats['success']} / "
                            f"{st.session_state.stats['errors']}",
                        )
                        await asyncio.sleep(0.5)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(run_batch_pipeline())
                except Exception as e:
                    update_ui_log(f"[FATAL] Batch pipeline error: {e}")
                finally:
                    loop.close()
                    st.session_state.stats["running"] = False
                    st.session_state.active_tab_index = 1
                    st.rerun()

        elif crawl_mode == "Keyword Search Lead Gen":
            update_ui_log(
                f"[SEARCH] Querying search engines for: '{target_input}'"
            )

            searcher = SearchEngineScraper()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            start_urls = []
            try:
                start_urls = loop.run_until_complete(
                    searcher.search(target_input, search_num_results)
                )
                update_ui_log(
                    f"[SEARCH] Found {len(start_urls)} potential leads."
                )
            except Exception as e:
                update_ui_log(f"[ERROR] Search failed: {e}")
            finally:
                loop.close()

            if not start_urls:
                st.error("Search failed to return valid URLs.")
                st.session_state.stats["running"] = False
            else:

                def single_callback(msg, scraper):
                    if not st.session_state.stats["running"]:
                        scraper.is_running = False
                    st.session_state.logs.append(msg)
                    if len(st.session_state.logs) > 500:
                        st.session_state.logs.pop(0)
                    st.session_state.stats["crawled"] = scraper.crawled_count
                    st.session_state.stats["success"] = scraper.success_count
                    st.session_state.stats["errors"] = scraper.error_count
                    st.session_state.scraped_emails = {
                        k: list(v) for k, v in scraper.scraped_emails.items()
                    }
                    st.session_state.scraped_numbers = scraper.scraped_numbers
                    st.session_state.scraped_leads = scraper.scraped_leads
                    log_text = "\n".join(st.session_state.logs)
                    log_area.markdown(
                        f'<div class="terminal-box">{log_text}</div>',
                        unsafe_allow_html=True,
                    )

                scraper = AsyncDualScraper(
                    start_urls=start_urls,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    concurrent_connections=concurrency,
                    internal_only=internal_only,
                    deobfuscate=deobfuscate,
                    scrape_emails=scrape_emails_flag,
                    scrape_phones=scrape_phones_flag,
                    email_validator=email_val,
                    phone_validator=phone_val,
                    update_callback=single_callback,
                )
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(scraper.start())
                except Exception as e:
                    update_ui_log(f"[FATAL] Crawl error: {e}")
                finally:
                    loop.close()
                    st.session_state.stats["running"] = False
                    st.session_state.active_tab_index = 1
                    st.rerun()
        else:
            # Direct URLs Mode
            start_urls = [
                url.strip() for url in target_input.split("\n") if url.strip()
            ]
            if not start_urls:
                st.error("No valid URLs supplied.")
                st.session_state.stats["running"] = False
            else:

                def direct_callback(msg, scraper):
                    if not st.session_state.stats["running"]:
                        scraper.is_running = False
                    st.session_state.logs.append(msg)
                    if len(st.session_state.logs) > 500:
                        st.session_state.logs.pop(0)
                    st.session_state.stats["crawled"] = scraper.crawled_count
                    st.session_state.stats["success"] = scraper.success_count
                    st.session_state.stats["errors"] = scraper.error_count
                    st.session_state.scraped_emails = {
                        k: list(v) for k, v in scraper.scraped_emails.items()
                    }
                    st.session_state.scraped_numbers = scraper.scraped_numbers
                    st.session_state.scraped_leads = scraper.scraped_leads
                    log_text = "\n".join(st.session_state.logs)
                    log_area.markdown(
                        f'<div class="terminal-box">{log_text}</div>',
                        unsafe_allow_html=True,
                    )

                scraper = AsyncDualScraper(
                    start_urls=start_urls,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    concurrent_connections=concurrency,
                    internal_only=internal_only,
                    deobfuscate=deobfuscate,
                    scrape_emails=scrape_emails_flag,
                    scrape_phones=scrape_phones_flag,
                    email_validator=email_val,
                    phone_validator=phone_val,
                    update_callback=direct_callback,
                )
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(scraper.start())
                except Exception as e:
                    update_ui_log(f"[FATAL] Crawl error: {e}")
                finally:
                    loop.close()
                    st.session_state.stats["running"] = False
                    st.session_state.active_tab_index = 1
                    st.rerun()


# ================= TAB 2: COMBINED LEADS TABLE =================
if active_tab == "Combined Leads Table":
    if st.session_state.scraped_companies:
        st.markdown("### 🏢 Batch Target Companies Contact Leads")
        df_comp = pd.DataFrame(st.session_state.scraped_companies)
        search_q = st.text_input(
            "Search companies (Name, Website, Email, or Phone)..."
        )
        if search_q:
            df_comp = df_comp[
                df_comp["Company Target"].str.contains(
                    search_q, case=False, na=False
                )
                | df_comp["Discovered Website"].str.contains(
                    search_q, case=False, na=False
                )
                | df_comp["Emails"].str.contains(
                    search_q, case=False, na=False
                )
                | df_comp["Phone Numbers"].str.contains(
                    search_q, case=False, na=False
                )
            ]

        st.dataframe(df_comp, use_container_width=True)
        st.info(f"Showing {len(df_comp)} target companies scraped.")

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        csv_comp = df_comp.to_csv(index=False, encoding="utf-8-sig").encode(
            "utf-8-sig"
        )
        with col_dl1:
            st.download_button(
                label="Download Company Leads CSV",
                data=csv_comp,
                file_name=(
                    f"company_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_comp.to_excel(writer, index=False, sheet_name="Company Leads")

            # Sheet 2: Flat list of all emails
            all_emails = []
            for item in st.session_state.scraped_companies:
                if item.get("Emails") and item["Emails"] != "-":
                    for em in item["Emails"].split(", "):
                        if em.strip():
                            all_emails.append(
                                {
                                    "Company Target": item["Company Target"],
                                    "Email": em.strip(),
                                    "Website": item["Discovered Website"],
                                }
                            )
            if all_emails:
                pd.DataFrame(all_emails).to_excel(
                    writer, index=False, sheet_name="All Emails"
                )

            # Sheet 3: Flat list of all phone numbers
            all_phones = []
            for item in st.session_state.scraped_companies:
                if item.get("Phone Numbers") and item["Phone Numbers"] != "-":
                    for ph in item["Phone Numbers"].split(", "):
                        if ph.strip():
                            all_phones.append(
                                {
                                    "Company Target": item["Company Target"],
                                    "Phone Number": ph.strip(),
                                    "WhatsApp Link": (
                                        f"https://wa.me/{ph.strip().lstrip('+')}"
                                    ),
                                    "Website": item["Discovered Website"],
                                }
                            )
            if all_phones:
                pd.DataFrame(all_phones).to_excel(
                    writer, index=False, sheet_name="All Phone Numbers"
                )

        excel_comp = buffer.getvalue()
        with col_dl2:
            st.download_button(
                label="Download Full Excel (Multi-Sheet)",
                data=excel_comp,
                file_name=(
                    f"company_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        json_comp = df_comp.to_json(orient="records", indent=4).encode("utf-8")
        with col_dl3:
            st.download_button(
                label="Download Company Leads JSON",
                data=json_comp,
                file_name=(
                    f"company_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".json"
                ),
                mime="application/json",
                use_container_width=True,
            )

    elif st.session_state.scraped_leads:
        st.markdown(
            "### Combined Business Leads (Email + Phone per Page/Website)"
        )
        rows = []
        for url, data in st.session_state.scraped_leads.items():
            emails_str = (
                ", ".join(data.get("emails", []))
                if data.get("emails")
                else "-"
            )
            phones_str = (
                ", ".join(data.get("phones", []))
                if data.get("phones")
                else "-"
            )
            rows.append(
                {
                    "Source URL": url,
                    "Domain": data.get("domain", ""),
                    "Emails Extracted": emails_str,
                    "Phone Numbers Extracted": phones_str,
                    "Total Emails": len(data.get("emails", [])),
                    "Total Phones": len(data.get("phones", [])),
                    "Discovered Time": data.get(
                        "first_seen",
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                    ),
                }
            )

        df_leads = pd.DataFrame(rows)
        search_q = st.text_input(
            "Search combined leads (URL, Domain, Email, or Phone)..."
        )
        if search_q:
            df_leads = df_leads[
                df_leads["Source URL"].str.contains(
                    search_q, case=False, na=False
                )
                | df_leads["Domain"].str.contains(
                    search_q, case=False, na=False
                )
                | df_leads["Emails Extracted"].str.contains(
                    search_q, case=False, na=False
                )
                | df_leads["Phone Numbers Extracted"].str.contains(
                    search_q, case=False, na=False
                )
            ]

        st.dataframe(df_leads, use_container_width=True)
        st.info(
            f"Showing {len(df_leads)} website lead pages with extracted "
            "contacts."
        )

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        csv_data = df_leads.to_csv(index=False).encode("utf-8")
        with col_dl1:
            st.download_button(
                label="Download Leads CSV",
                data=csv_data,
                file_name=(
                    f"combined_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_leads.to_excel(writer, index=False, sheet_name="Combined Leads")
            if st.session_state.scraped_emails:
                email_rows = [
                    {
                        "Email": em,
                        "Domain": em.split("@")[-1] if "@" in em else "",
                        "Source URLs": ", ".join(urls),
                        "Discovered": datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    }
                    for em, urls in st.session_state.scraped_emails.items()
                ]
                pd.DataFrame(email_rows).to_excel(
                    writer, index=False, sheet_name="Emails"
                )

            if st.session_state.scraped_numbers:
                phone_rows = [
                    {
                        "Phone Number": e164,
                        "National Format": pdata.get("national", ""),
                        "Operator": pdata.get("operator", ""),
                        "Type": pdata.get("type", ""),
                        "WhatsApp Link": pdata.get("wa_link", "-"),
                        "Source URLs": ", ".join(pdata.get("sources", [])),
                        "Discovered": datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    }
                    for e164, pdata in st.session_state.scraped_numbers.items()
                ]
                pd.DataFrame(phone_rows).to_excel(
                    writer, index=False, sheet_name="Phone Numbers"
                )

        excel_data = buffer.getvalue()
        with col_dl2:
            st.download_button(
                label="Download Full Excel (Multi-Sheet)",
                data=excel_data,
                file_name=(
                    "unified_scrape_data_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        json_data = df_leads.to_json(orient="records", indent=4).encode(
            "utf-8"
        )
        with col_dl3:
            st.download_button(
                label="Download Leads JSON",
                data=json_data,
                file_name=(
                    f"combined_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".json"
                ),
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.warning(
            "No leads extracted yet. Start crawling to populate contacts."
        )


# ================= TAB 3: SCRAPED EMAILS TABLE =================
if active_tab == "Scraped Emails Table":
    st.markdown("### Extracted & Validated Email Addresses")

    if st.session_state.scraped_emails:
        rows = []
        for email, urls in st.session_state.scraped_emails.items():
            domain = email.split("@")[-1] if "@" in email else "unknown"
            urls_str = (
                ", ".join(urls) if isinstance(urls, (list, set)) else str(urls)
            )
            rows.append(
                {
                    "Email": email,
                    "Domain": domain,
                    "Source URLs": urls_str,
                    "First Discovered": datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
            )

        df_emails = pd.DataFrame(rows)
        search_q = st.text_input("Search emails table (email or domain)...")
        if search_q:
            df_emails = df_emails[
                df_emails["Email"].str.contains(search_q, case=False, na=False)
                | df_emails["Domain"].str.contains(
                    search_q, case=False, na=False
                )
                | df_emails["Source URLs"].str.contains(
                    search_q, case=False, na=False
                )
            ]

        st.dataframe(df_emails, use_container_width=True)
        st.info(f"Showing {len(df_emails)} validated unique email addresses.")

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        csv_data = df_emails.to_csv(index=False).encode("utf-8")
        with col_dl1:
            st.download_button(
                label="Download Emails CSV",
                data=csv_data,
                file_name=(
                    f"scraped_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_emails.to_excel(writer, index=False, sheet_name="Emails")
        excel_data = buffer.getvalue()
        with col_dl2:
            st.download_button(
                label="Download Emails Excel",
                data=excel_data,
                file_name=(
                    f"scraped_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        json_data = df_emails.to_json(orient="records", indent=4).encode(
            "utf-8"
        )
        with col_dl3:
            st.download_button(
                label="Download Emails JSON",
                data=json_data,
                file_name=(
                    f"scraped_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    ".json"
                ),
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.warning(
            "No emails extracted yet. Run the scraper to populate results."
        )


# ================= TAB 4: SCRAPED NUMBERS TABLE =================
if active_tab == "Scraped Numbers Table":
    st.markdown("### Extracted & Validated Indonesian Phone Numbers")

    if st.session_state.scraped_numbers:
        rows = []
        for e164, data in st.session_state.scraped_numbers.items():
            sources = data.get("sources", [])
            urls_str = (
                ", ".join(sources)
                if isinstance(sources, (list, set))
                else str(sources)
            )
            rows.append(
                {
                    "Phone Number": e164,
                    "National Format": data.get("national", ""),
                    "Carrier / Operator": data.get("operator", "Unknown"),
                    "Type": data.get("type", "Mobile"),
                    "WhatsApp Link": data.get("wa_link", "-"),
                    "Source URLs": urls_str,
                    "First Discovered": datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                }
            )

        df_nums = pd.DataFrame(rows)
        search_q = st.text_input(
            "Search phone numbers table (number, carrier, type, or URL)..."
        )
        if search_q:
            df_nums = df_nums[
                df_nums["Phone Number"].str.contains(
                    search_q, case=False, na=False
                )
                | df_nums["National Format"].str.contains(
                    search_q, case=False, na=False
                )
                | df_nums["Carrier / Operator"].str.contains(
                    search_q, case=False, na=False
                )
                | df_nums["Type"].str.contains(search_q, case=False, na=False)
                | df_nums["Source URLs"].str.contains(
                    search_q, case=False, na=False
                )
            ]

        st.dataframe(df_nums, use_container_width=True)
        st.info(
            f"Showing {len(df_nums)} validated unique "
            "Indonesian phone numbers."
        )

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        csv_data = df_nums.to_csv(index=False).encode("utf-8")
        with col_dl1:
            st.download_button(
                label="Download Numbers CSV",
                data=csv_data,
                file_name=(
                    "scraped_phone_numbers_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                ),
                mime="text/csv",
                use_container_width=True,
            )

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_nums.to_excel(writer, index=False, sheet_name="Phone Numbers")
        excel_data = buffer.getvalue()
        with col_dl2:
            st.download_button(
                label="Download Numbers Excel",
                data=excel_data,
                file_name=(
                    "scraped_phone_numbers_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

        json_data = df_nums.to_json(orient="records", indent=4).encode("utf-8")
        with col_dl3:
            st.download_button(
                label="Download Numbers JSON",
                data=json_data,
                file_name=(
                    "scraped_phone_numbers_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                ),
                mime="application/json",
                use_container_width=True,
            )
    else:
        st.warning(
            "No phone numbers extracted yet. Run scraper to populate results."
        )


# ================= TAB 5: PERFORMANCE ANALYTICS =================
if active_tab == "Performance Analytics":
    st.markdown("### Telecom, Email & Crawling Analytics")

    if (
        st.session_state.scraped_emails
        or st.session_state.scraped_numbers
        or st.session_state.scraped_companies
    ):
        col_vis1, col_vis2 = st.columns(2)

        with col_vis1:
            st.markdown("#### Top Telco Operators & Carriers")
            if st.session_state.scraped_numbers:
                operators = [
                    data.get("operator", "Unknown")
                    for data in st.session_state.scraped_numbers.values()
                ]
                op_df = (
                    pd.DataFrame(operators, columns=["Operator"])
                    .value_counts()
                    .reset_index(name="Count")
                )
                st.bar_chart(op_df.set_index("Operator").head(10))
            else:
                st.info("No phone number data for carrier analysis.")

        with col_vis2:
            st.markdown("#### Top Email Domain Providers")
            if st.session_state.scraped_emails:
                domains = [
                    em.split("@")[-1]
                    for em in st.session_state.scraped_emails.keys()
                    if "@" in em
                ]
                domain_df = (
                    pd.DataFrame(domains, columns=["Domain"])
                    .value_counts()
                    .reset_index(name="Count")
                )
                st.bar_chart(domain_df.set_index("Domain").head(10))
            else:
                st.info("No email data for domain analysis.")

        col_vis3, col_vis4 = st.columns(2)
        with col_vis3:
            st.markdown("#### Number Type Breakdown (Mobile vs Landline)")
            if st.session_state.scraped_numbers:
                types = [
                    data.get("type", "Mobile")
                    for data in st.session_state.scraped_numbers.values()
                ]
                type_df = (
                    pd.DataFrame(types, columns=["Type"])
                    .value_counts()
                    .reset_index(name="Count")
                )
                st.bar_chart(type_df.set_index("Type"))
            else:
                st.info("No phone types recorded.")

        with col_vis4:
            st.markdown("#### Crawl HTTP Status Breakdown")
            success = st.session_state.stats["success"]
            errors = st.session_state.stats["errors"]
            if success + errors > 0:
                stats_df = pd.DataFrame(
                    {
                        "Status": [
                            "Success (200 OK)",
                            "Errors / Blocked / Timeout",
                        ],
                        "Count": [success, errors],
                    }
                )
                st.dataframe(stats_df, use_container_width=True)
            else:
                st.info("No network requests executed yet.")
    else:
        st.warning(
            "No analytics data available. Start crawling to view charts."
        )
