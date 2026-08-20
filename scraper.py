"""SIBRA Unified Email & Phone Scraper - Main Entry Point.

Provides CLI and Web dashboard launcher for simultaneous extraction
of email addresses and Indonesian phone numbers.
"""

import asyncio
import subprocess
import sys
from datetime import datetime

import pandas as pd
import pyfiglet

from batch_scraper import main as run_batch_main
from scraper_engine import (
    AsyncDualScraper,
    EmailValidator,
    PhoneNumberValidator,
)


def run_streamlit():
    """Launch the Streamlit web dashboard."""
    print("[+] Launching Streamlit Web UI Dashboard...")
    try:
        subprocess.run(["streamlit", "run", "app.py"], check=False)
    except KeyboardInterrupt:
        print("\n[-] Streamlit Server Stopped.")


def run_cli():
    """Run interactive console CLI scraper for single URL or keyword."""
    print(pyfiglet.figlet_format("SIBRA v2", font="slant"))
    print("=== SIBRA UNIFIED EMAIL & PHONE SCRAPER (CLI Mode) ===\n")

    print("[?] Select Target Extraction:")
    print("  1. Both Emails & Phone Numbers (Simultaneous)")
    print("  2. Emails Only")
    print("  3. Phone Numbers Only")
    target_choice = input("[+] Choice (1-3, default 1): ").strip() or "1"

    scrape_emails = target_choice in ("1", "2")
    scrape_phones = target_choice in ("1", "3")

    start_url = input("\n[+] Please enter target URL: ").strip()
    if not start_url:
        print("[-] Invalid URL!")
        return

    try:
        max_pages = int(
            input("[+] Enter max pages to crawl (default 50): ") or 50
        )
        max_depth = int(input("[+] Enter crawl depth (default 1): ") or 1)
        concurrency = int(
            input("[+] Enter concurrent connections (default 15): ") or 15
        )
    except ValueError:
        print("[-] Invalid input numbers! Using defaults.")
        max_pages = 50
        max_depth = 1
        concurrency = 15

    print(
        "\n[+] Crawling in progress... "
        "Press Ctrl+C to stop and save results.\n"
    )

    email_val = EmailValidator()
    phone_val = PhoneNumberValidator()

    def console_callback(message, _scraper):
        print(message)

    scraper = AsyncDualScraper(
        start_urls=[start_url],
        max_depth=max_depth,
        max_pages=max_pages,
        concurrent_connections=concurrency,
        internal_only=True,
        deobfuscate=True,
        scrape_emails=scrape_emails,
        scrape_phones=scrape_phones,
        email_validator=email_val,
        phone_validator=phone_val,
        update_callback=console_callback,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(scraper.start())
    except KeyboardInterrupt:
        print("\n[-] Crawl interrupted by user!")
    finally:
        loop.close()

    print("\n====================================")
    print("SCRAPING COMPLETED!")
    print("====================================")

    if scrape_emails:
        print(f"\n[+] {len(scraper.scraped_emails)} unique verified emails:")
        for email in sorted(scraper.scraped_emails.keys()):
            sources = ", ".join(scraper.scraped_emails[email])
            print(f"  • {email} (From: {sources})")

    if scrape_phones:
        print(
            f"\n[+] {len(scraper.scraped_numbers)} "
            "unique verified Indonesian phone numbers:"
        )
        for num, data in sorted(scraper.scraped_numbers.items()):
            nat = data.get("national", "-")
            op = data.get("operator", "-")
            ntype = data.get("type", "-")
            wa = data.get("wa_link", "-")
            print(f"  • {num} | {nat} | {op} | {ntype} | WA: {wa}")

    # Prompt to export
    if scraper.scraped_emails or scraper.scraped_numbers:
        save_choice = (
            input("\n[?] Export results to CSV/Excel? (y/n, default y): ")
            .strip()
            .lower()
            or "y"
        )
        if save_choice == "y":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save combined leads
            lead_rows = []
            if scraper.scraped_leads:
                for url, ldata in scraper.scraped_leads.items():
                    lead_rows.append(
                        {
                            "Source URL": url,
                            "Domain": ldata.get("domain", ""),
                            "Emails": ", ".join(ldata.get("emails", [])),
                            "Phones": ", ".join(ldata.get("phones", [])),
                            "Total Emails": len(ldata.get("emails", [])),
                            "Total Phones": len(ldata.get("phones", [])),
                        }
                    )
                df_leads = pd.DataFrame(lead_rows)
                leads_file = f"combined_leads_{timestamp}.csv"
                df_leads.to_csv(leads_file, index=False)
                print(f"[✓] Saved combined leads to {leads_file}")

            # Save full multi-sheet Excel
            excel_file = f"scraped_data_{timestamp}.xlsx"
            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                if scraper.scraped_leads:
                    pd.DataFrame(lead_rows).to_excel(
                        writer, index=False, sheet_name="Combined Leads"
                    )
                if scraper.scraped_emails:
                    email_rows = [
                        {
                            "Email": em,
                            "Domain": em.split("@")[-1] if "@" in em else "",
                            "Source URLs": ", ".join(urls),
                        }
                        for em, urls in scraper.scraped_emails.items()
                    ]
                    pd.DataFrame(email_rows).to_excel(
                        writer, index=False, sheet_name="Emails"
                    )
                if scraper.scraped_numbers:
                    phone_rows = [
                        {
                            "Phone Number": e164,
                            "National Format": pdata.get("national", ""),
                            "Operator": pdata.get("operator", ""),
                            "Type": pdata.get("type", ""),
                            "WhatsApp Link": pdata.get("wa_link", "-"),
                            "Source URLs": ", ".join(pdata.get("sources", [])),
                        }
                        for e164, pdata in scraper.scraped_numbers.items()
                    ]
                    pd.DataFrame(phone_rows).to_excel(
                        writer, index=False, sheet_name="Phone Numbers"
                    )

            print(f"[✓] Saved full multi-sheet dataset to {excel_file}")
    print()


def run_batch():
    """Launch the batch company target scraper."""
    run_batch_main()


def main():
    """Main program entry dispatcher."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cli":
            run_cli()
            return
        if sys.argv[1] == "--web":
            run_streamlit()
            return
        if sys.argv[1] == "--batch":
            run_batch()
            return

    print(pyfiglet.figlet_format("SIBRA v2", font="slant"))
    print("Welcome to SIBRA Unified Email & Phone Scraper v2.0")
    print("1. Launch Streamlit Web UI (Recommended)")
    print("2. Run Console CLI Scraper (Single URL / Keyword)")
    print("3. Run Batch Company Targets Scraper (100 Focus Targets)")

    choice = input("\n[+] Select an option (1-3, default 1): ").strip()
    if choice == "2":
        run_cli()
    elif choice == "3":
        run_batch()
    else:
        run_streamlit()


if __name__ == "__main__":
    main()
