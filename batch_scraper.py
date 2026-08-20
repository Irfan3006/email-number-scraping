"""Batch Company Target Scraper.

Automated runner that searches candidate websites and extracts verified
emails, Indonesian phone numbers, and WhatsApp links for target companies.
"""

import asyncio
import os
import sys
from datetime import datetime

import pandas as pd
import pyfiglet

from scraper_engine import (
    AsyncDualScraper,
    EmailValidator,
    PhoneNumberValidator,
    SearchEngineScraper,
)


class BatchCompanyScraper:
    """Automated batch runner for multi-company contact extraction."""

    def __init__(
        self,
        targets_file="targets.txt",
        max_pages_per_company=15,
        max_depth=1,
        concurrency=10,
        output_excel="target_companies_leads.xlsx",
        output_csv="target_companies_leads.csv",
    ):
        """Initialize the batch company scraper with crawling parameters."""
        self.targets_file = targets_file
        self.max_pages_per_company = max_pages_per_company
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.output_excel = output_excel
        self.output_csv = output_csv

        self.searcher = SearchEngineScraper()
        self.email_val = EmailValidator()
        self.phone_val = PhoneNumberValidator()
        self.results = []

    def load_targets(self) -> list:
        """Load and deduplicate target company names from file."""
        if not os.path.exists(self.targets_file):
            print(f"[-] File {self.targets_file} not found!")
            return []
        with open(self.targets_file, "r", encoding="utf-8") as f:
            lines = [
                line.strip()
                for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
        # Deduplicate while preserving order
        unique_targets = list(dict.fromkeys(lines))
        return unique_targets

    def save_checkpoint(self):
        """Save current collected results to Excel and CSV."""
        if not self.results:
            return

        df = pd.DataFrame(self.results)
        df.to_csv(self.output_csv, index=False, encoding="utf-8-sig")

        try:
            with pd.ExcelWriter(
                self.output_excel, engine="openpyxl"
            ) as writer:
                df.to_excel(writer, index=False, sheet_name="Company Leads")

                # Sheet 2: Flat list of all emails
                all_emails = []
                for item in self.results:
                    if item.get("Emails"):
                        for em in item["Emails"].split(", "):
                            if em:
                                all_emails.append(
                                    {
                                        "Company": item["Company Target"],
                                        "Email": em,
                                        "Website": item["Discovered Website"],
                                    }
                                )
                if all_emails:
                    pd.DataFrame(all_emails).to_excel(
                        writer, index=False, sheet_name="All Emails"
                    )

                # Sheet 3: Flat list of all phone numbers
                all_phones = []
                for item in self.results:
                    if item.get("Phone Numbers"):
                        for ph in item["Phone Numbers"].split(", "):
                            if ph:
                                all_phones.append(
                                    {
                                        "Company": item["Company Target"],
                                        "Phone Number": ph,
                                        "WhatsApp Link": (
                                            f"https://wa.me/{ph.lstrip('+')}"
                                        ),
                                        "Website": item["Discovered Website"],
                                    }
                                )
                if all_phones:
                    pd.DataFrame(all_phones).to_excel(
                        writer, index=False, sheet_name="All Phone Numbers"
                    )
        except Exception as e:
            print(f"[!] Warning saving Excel: {e}")

    async def process_company(
        self, company_name: str, index: int, total: int
    ) -> dict:
        """Search website and scrape contacts for a single company."""
        print(
            f"\n[{index}/{total}] [SEARCH] "
            f"Finding websites for: '{company_name}'..."
        )

        try:
            search_urls = await self.searcher.search_company(company_name)
        except Exception as e:
            print(f"  [!] Search error for {company_name}: {e}")
            search_urls = []

        if not search_urls:
            print(f"  [-] No candidate website found for '{company_name}'")
            return {
                "Company Target": company_name,
                "Status": "Website Not Found",
                "Discovered Website": "-",
                "Emails": "",
                "Phone Numbers": "",
                "WhatsApp Links": "",
                "Carriers / Types": "",
                "Total Emails": 0,
                "Total Phones": 0,
                "Scraped Pages": 0,
                "Source URLs": "",
                "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

        print(f"  [+] Found candidate websites: {', '.join(search_urls[:2])}")
        print(
            f"  [+] Crawling target pages (Depth {self.max_depth}, "
            f"Max {self.max_pages_per_company} pages)..."
        )

        scraper = AsyncDualScraper(
            start_urls=search_urls[:3],
            max_depth=self.max_depth,
            max_pages=self.max_pages_per_company,
            concurrent_connections=self.concurrency,
            internal_only=True,
            deobfuscate=True,
            scrape_emails=True,
            scrape_phones=True,
            email_validator=self.email_val,
            phone_validator=self.phone_val,
        )

        try:
            await scraper.start()
        except Exception as e:
            print(f"  [!] Scraper error: {e}")

        emails_list = sorted(list(scraper.scraped_emails.keys()))
        phones_list = sorted(
            [p["e164"] for p in scraper.scraped_numbers.values()]
        )
        wa_links = sorted(
            [
                p["wa_link"]
                for p in scraper.scraped_numbers.values()
                if p.get("wa_link") and p["wa_link"] != "-"
            ]
        )
        operators = sorted(
            list(
                {
                    f"{p['operator']} ({p['type']})"
                    for p in scraper.scraped_numbers.values()
                }
            )
        )
        sources = sorted(list(scraper.visited_urls))

        primary_website = search_urls[0] if search_urls else "-"
        status = (
            "Success (Data Found)"
            if (emails_list or phones_list)
            else "Scraped (No Contacts Found)"
        )

        print(
            f"  [OK] Result for '{company_name}': "
            f"{len(emails_list)} emails, {len(phones_list)} phones found."
        )
        if emails_list:
            print(f"      Emails: {', '.join(emails_list[:3])}")
        if phones_list:
            print(f"      Phones: {', '.join(phones_list[:3])}")

        return {
            "Company Target": company_name,
            "Status": status,
            "Discovered Website": primary_website,
            "Emails": ", ".join(emails_list),
            "Phone Numbers": ", ".join(phones_list),
            "WhatsApp Links": ", ".join(wa_links),
            "Carriers / Types": ", ".join(operators),
            "Total Emails": len(emails_list),
            "Total Phones": len(phones_list),
            "Scraped Pages": scraper.crawled_count,
            "Source URLs": ", ".join(sources[:5]),
            "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

    async def run(self, max_targets=None):
        """Execute the batch process across target companies."""
        targets = self.load_targets()
        if max_targets:
            targets = targets[:max_targets]

        total = len(targets)
        print(
            f"\n[+] Loaded {total} target companies from '{self.targets_file}'"
        )
        print(
            f"[+] Output will be saved to: "
            f"{self.output_excel} & {self.output_csv}\n"
        )

        for idx, company in enumerate(targets, 1):
            res = await self.process_company(company, idx, total)
            self.results.append(res)
            self.save_checkpoint()
            # Brief polite pause between company searches
            await asyncio.sleep(1)

        print("\n" + "=" * 50)
        print("BATCH TARGET SCRAPING COMPLETED!")
        print(f"Total Companies Processed: {len(self.results)}")
        found_count = sum(
            1
            for r in self.results
            if r["Total Emails"] > 0 or r["Total Phones"] > 0
        )
        print(
            f"Companies with Contacts Found: {found_count}/{len(self.results)}"
        )
        print(
            f"Results saved to:\n"
            f"  * {self.output_excel}\n"
            f"  * {self.output_csv}"
        )
        print("=" * 50 + "\n")


def main():
    """Main function for CLI batch company scraping."""
    print(pyfiglet.figlet_format("SIBRA v2", font="slant"))
    print("=== BATCH COMPANY TARGET SCRAPER ===\n")

    targets_file = "targets.txt"
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        targets_file = sys.argv[1]

    runner = BatchCompanyScraper(
        targets_file=targets_file,
        max_pages_per_company=15,
        max_depth=1,
        concurrency=10,
    )

    targets = runner.load_targets()
    print(f"[+] Found {len(targets)} companies in {targets_file}")
    print("Options:")
    print("  1. Run All Companies (1 - 100)")
    print("  2. Test Run First 5 Companies")
    print("  3. Run Custom Number of Companies")

    choice = input("\n[+] Select an option (1-3, default 1): ").strip() or "1"
    max_count = None
    if choice == "2":
        max_count = 5
    elif choice == "3":
        try:
            max_count = int(input("[+] How many companies to scrape? "))
        except ValueError:
            max_count = 10

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(runner.run(max_targets=max_count))
    except KeyboardInterrupt:
        print(
            "\n[-] Batch process interrupted by user! Partial results saved."
        )
    finally:
        loop.close()


if __name__ == "__main__":
    main()
