"""SIBRA Unified Scraper Engine.

Core asynchronous scraping engine with dual extraction capabilities for email
addresses and Indonesian mobile/landline telephone numbers. Includes strict
domain boundary enforcement and anti-false-positive validators.
"""

import asyncio
import base64
import random
import re
import urllib.parse
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup

# =====================================================================
# GLOBAL BLACKLIST DOMAINS (Blogs, News, Media, Virtual Offices, Forums)
# =====================================================================
GLOBAL_BLACKLIST_DOMAINS = {
    # Virtual Office & Shared Services (Causes False Positives on "PT" queries)
    "voffice.co.id",
    "servcorp.co.id",
    "regus.com",
    "marquee.co.id",
    "ceosupite.com",
    "uptown.id",
    "wellspaces.co",
    "greenhub.co.id",
    "uniongroup.id",
    "gapuraoffice.biz",
    # Movie, Entertainment, Cinema & Streaming Sites
    "d21.team",
    "layarkaca21",
    "lk21",
    "indoxxi",
    "21cineplex.com",
    "cgv.id",
    "cinepolis.co.id",
    "jadwalnonton.com",
    "poki.com",
    "poki.zone",
    "poki.ac",
    "ea.com",
    "steamcommunity.com",
    # News, Magazines, Media & Press Agencies
    "antaranews.com",
    "antara.co.id",
    "fortune.com",
    "sohu.com",
    "cnyes.com",
    "bbc.com",
    "cnn.com",
    "cnbcindonesia.com",
    "kompas.com",
    "detik.com",
    "tribunnews.com",
    "tempo.co",
    "kumparan.com",
    "idntimes.com",
    "liputan6.com",
    "merdeka.com",
    "kaskus.co.id",
    "thesun.co.uk",
    "bloomberg.com",
    "reuters.com",
    "investor.id",
    "bisnis.com",
    "kontan.co.id",
    "jawapos.com",
    # Web Hosting Providers & Domain Registrars
    "rumahweb.com",
    "niagahoster.co.id",
    "idwebhost.com",
    "qwords.com",
    "hostinger.com",
    "hostinger.co.id",
    "domainesia.com",
    "dewaweb.com",
    "cpanel.net",
    "domainku.xyz",
    "whois.com",
    "godaddy.com",
    "namecheap.com",
    "cloudflare.com",
    "siteground.com",
    # Search Engines, Tech Platforms, Software & Cloud
    "google.com",
    "google.co.id",
    "google.co.kr",
    "google.com.sg",
    "googleapis.com",
    "gstatic.com",
    "design.google",
    "about.google",
    "blog.google",
    "google.dev",
    "googleapps.com",
    "bing.com",
    "yahoo.com",
    "duckduckgo.com",
    "yandex.com",
    "baidu.com",
    "zhidao.baidu.com",
    "zhihu.com",
    "microsoft.com",
    "apple.com",
    "tableau.com",
    "genius.com",
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "stackoverflow.com",
    "stackexchange.com",
    "tex.stackexchange.com",
    "dlang.org",
    "geeksforgeeks.org",
    "design.com",
    "canva.com",
    "figma.com",
    "freepik.com",
    "vecteezy.com",
    "logomaker.com",
    "griyabayar.com",
    "jsdelivr.net",
    "unpkg.com",
    "w3schools.com",
    "sentry.io",
    "wordpress.org",
    "wordpress.com",
    "elementor.com",
    "yoast.com",
    "gravatar.com",
    "w3.org",
    "schema.org",
    # Dictionaries, Encyclopedias, Education, Health, NGOs & Government
    "wikipedia.org",
    "kbbi.web.id",
    "kbbi.co.id",
    "dictionary.cambridge.org",
    "cambridge.org",
    "dictionary.com",
    "merriam-webster.com",
    "investopedia.com",
    "udemy.com",
    "coursera.org",
    "ruangguru.com",
    "zenius.net",
    "halodoc.com",
    "alodokter.com",
    "klikdokter.com",
    "elephantconservation.org",
    "unib.ac.id",
    "ac.id",
    "edu",
    "gov.in",
    "go.id",
    "ahu.go.id",
    "ptp.ahu.go.id",
    "kemenkumham.go.id",
    "pajak.go.id",
    "kemendag.go.id",
    "pom.go.id",
    # Unrelated Companies, Insurance, Bedding, Foreign Tourism, Lottery
    "asuransibintang.com",
    "comforta.co.id",
    "massindo.com",
    "terrawaterindonesia.com",
    "spesolution.com",
    "gemilangindonesia.or.id",
    "naramachi.co.jp",
    "narashikanko.or.jp",
    "anugrah.co.in",
    "anugrah.net",
    "himalaya.com",
    "comfrt.com",
    "colossal.net",
    "sinarjuli.com",
    "tntenders.gov.in",
    "upwill.com.sg",
    "geekzag.com",
    "helpdeskgeek.com",
    "galleri.com",
    "anuegroup.com.tw",
    "dior.com",
    "justanswer.com",
    "gurubelajarku.com",
    "bimobject.com",
    "i2symbol.com",
    "thoughtco.com",
    "yellowpages.id",
    "traveloka.com",
    "tiket.com",
    "travels.id",
    "daisonet.com",
    "royalmail.com",
    "miniwebtool.com",
    "islamweb.net",
    "fukui7samurai.site",
    "yunxyunnoouchi.com",
    "visitbrescia.it",
    "visitnara.jp",
    "japan-guide.com",
    "foodierate.com",
    "commentcamarche.net",
    "picjjang.com",
    "xahuapu.net",
    "morsewords.com",
    "scribd.com",
    "quora.com",
    "reddit.com",
    # Shopping Malls & Retail Centers
    "emporiumpluit.com",
    "pluitjunction.com",
    "mallkelapagading.com",
    "senayancity.com",
    "grand-indonesia.com",
    "pondokindahmall.co.id",
    "centralparkjakarta.com",
    "taman-anggrek-mall.com",
    "pacificplace.co.id",
    "plaza-senayan.com",
    "gandariacity.co.id",
    "kotakasablanka.co.id",
    # Generic Business Directories
    "findglocal.com",
    "semuabis.com",
    "infobel.com",
    "local.infobel.co.id",
    "sgpgrid.com",
    "emis.com",
    "yellowpages.co.id",
    "tokopedia.com",
    "shopee.co.id",
    "bukalapak.com",
    "lazada.co.id",
    "blibli.com",
    "rumah123.com",
    "lamudi.co.id",
    "olx.co.id",
    "indotrading.com",
    "indonetwork.co.id",
}

BLOCKED_URL_PATHS = [
    "/blog/",
    "/berita/",
    "/news/",
    "/artikel/",
    "/genre/",
    "/film/",
    "/bioskop/",
    "/author/",
    "/tag/",
    "/category/",
    "/fatawa/",
    "/question/",
    "/forum/",
    "/thread/",
    "/topic/",
    "/wiki/",
    "/login",
    "/admin",
    "/signin",
    "/register",
    "/cart",
    "/checkout",
    "/terms",
    "/privacy",
    "/disclaimer",
    "/policy",
    "/episode/",
    "/courses/",
]

BLOCKED_TLDS = {
    ".google",
    ".jp",
    ".or.jp",
    ".co.jp",
    ".in",
    ".co.in",
    ".tw",
    ".com.tw",
    ".cn",
    ".com.cn",
    ".hk",
    ".sg",
    ".com.sg",
    ".my",
    ".com.my",
    ".th",
    ".co.th",
    ".uk",
    ".co.uk",
    ".es",
    ".de",
    ".fr",
    ".it",
    ".ru",
    ".br",
    ".com.br",
    ".or.id",
    ".org",
    ".gov",
    ".edu",
}

UNRELATED_INDUSTRY_KEYWORDS = {
    "asuransi",
    "insurance",
    "springbed",
    "kasur",
    "bedding",
    "water filter",
    "air minum",
    "fintech",
    "software",
    "zakat",
    "infaq",
    "donasi",
    "yayasan",
    "podcast",
    "audiobook",
    "wisata",
    "sightseeing",
    "travel",
    "tiket",
}


class CompanyRelevanceValidator:
    """Validates whether a candidate domain strictly belongs to the company."""

    INDUSTRY_KEYWORDS = {
        "marmer",
        "marble",
        "granit",
        "granite",
        "onyx",
        "travertine",
        "andesit",
        "batu alam",
        "natural stone",
        "sintered stone",
        "quartz",
        "keramik",
        "ceramica",
        "kaca",
        "glass",
        "indoglass",
        "glassindo",
        "tempered",
        "laminated",
        "mirror",
        "cermin",
        "aluminium",
        "alumindo",
        "facade",
        "fasad",
        "kusen",
        "jendela",
        "pintu",
        "lantai",
        "flooring",
        "dinding",
        "wall",
        "slab",
        "tile",
        "ubin",
        "interior",
        "arsitektur",
        "kontraktor",
        "supplier",
        "distributor",
        "pabrik",
        "industri",
        "proyek",
        "showroom",
        "workshop",
        "tambang",
        "quarry",
    }

    LEGAL_ENTITY_STOP_WORDS = {
        "pt",
        "cv",
        "tbk",
        "ud",
        "ltd",
        "inc",
        "perseroan",
        "terbatas",
        "corp",
        "corporation",
    }

    def get_brand_tokens(self, company_name: str) -> list:
        """Extract brand tokens from company name by removing entity words."""
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", company_name).lower()
        words = [w.strip() for w in cleaned.split() if w.strip()]
        brand_tokens = [
            w
            for w in words
            if w not in self.LEGAL_ENTITY_STOP_WORDS and len(w) >= 2
        ]
        return brand_tokens

    def is_domain_brand_match(self, domain: str, company_name: str) -> bool:
        """Check if domain matches the brand name tokens."""
        domain_clean = (
            domain.lower()
            .replace("www.", "")
            .replace("-", "")
            .replace(".", "")
        )
        brand_tokens = self.get_brand_tokens(company_name)
        if not brand_tokens:
            return False

        if len(brand_tokens) >= 2:
            compound = "".join(brand_tokens)
            if compound in domain_clean:
                return True
            if (
                brand_tokens[-1] in ("indonesia", "group", "company")
                and "".join(brand_tokens[:-1]) in domain_clean
            ):
                return True
            if (
                len(brand_tokens) > 2
                and "".join(brand_tokens[:2]) in domain_clean
            ):
                return True
            return False

        token = brand_tokens[0]
        if len(token) >= 4 and token in domain_clean:
            return True
        return False

    def is_url_strictly_blocked(self, url: str) -> bool:
        """Return True if URL matches global blacklists or blocked TLDs."""
        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            if any(
                domain == b or domain.endswith("." + b) or b in domain
                for b in GLOBAL_BLACKLIST_DOMAINS
            ):
                return True
            for tld in BLOCKED_TLDS:
                if domain.endswith(tld):
                    return True
            path = parsed.path.lower()
            if any(bp in path for bp in BLOCKED_URL_PATHS):
                return True
        except Exception:
            return True
        return False

    def is_page_relevant(
        self,
        html_text: str,
        page_title: str,
        company_name: str,
        domain: str,
    ) -> bool:
        """Validate if page content matches company name and industry."""
        text_lower = (page_title + " " + html_text[:5000]).lower()

        # Reject if page is dominated by unrelated industries
        if any(ukw in text_lower for ukw in UNRELATED_INDUSTRY_KEYWORDS):
            return False

        if self.is_domain_brand_match(domain, company_name):
            return True

        brand_tokens = self.get_brand_tokens(company_name)
        brand_found = any(token in text_lower for token in brand_tokens)
        if not brand_found:
            return False

        industry_found = any(kw in text_lower for kw in self.INDUSTRY_KEYWORDS)
        return industry_found


class EmailValidator:
    """High-accuracy email validator with strict anti-false-positive rules."""

    def __init__(
        self, custom_blacklist_domains=None, custom_blacklist_emails=None
    ):
        """Initialize validator with standard and custom blacklists."""
        self.blacklist_domains = set(GLOBAL_BLACKLIST_DOMAINS)
        self.blacklist_domains.update(
            {
                "example.com",
                "example.org",
                "example.net",
                "test.com",
                "sample.com",
                "dummy.com",
                "yourdomain.com",
                "domain.com",
                "placeholder.com",
                "tempmail.com",
                "contoh.com",
                "contoh.id",
                "sitename.com",
                "mywebsite.com",
                "website.com",
                "email.com",
                "mail.com",
                "company.com",
                "mysite.com",
                "yoursite.com",
            }
        )
        if custom_blacklist_domains:
            self.blacklist_domains.update(custom_blacklist_domains)

        self.blacklist_emails = {
            "email@example.com",
            "user@example.com",
            "your@email.com",
            "info@example.com",
            "username@domain.com",
            "test@test.com",
            "test@example.com",
            "admin@example.com",
            "git@github.com",
            "noreply@github.com",
            "support@github.com",
            "hello@example.com",
            "webmaster@domain.com",
            "admin@domain.com",
            "postmaster@domain.com",
            "test@gmail.com",
            "yourname@gmail.com",
            "john.doe@gmail.com",
            "john@example.com",
            "email@contoh.com",
            "admin@contoh.com",
            "contoh@contoh.com",
            "info@contoh.com",
            "email@contoh.id",
            "admin@contoh.id",
            "contoh@contoh.id",
            "info@contoh.id",
            "name@company.com",
            "admin@yourdomain.com",
            "info@yourdomain.com",
            "support@yourdomain.com",
            "contact@yourdomain.com",
            "sales@yourdomain.com",
            "user@domain.com",
            "sample@email.com",
            "cs@voffice.co.id",
            "jobs@voffice.co.id",
            "redaksi@antaranews.com",
            "cs@asuransibintang.com",
            "liberdisaren@gmail.com",
            "hello@terrawaterindonesia.com",
        }
        if custom_blacklist_emails:
            self.blacklist_emails.update(custom_blacklist_emails)

        self.asset_prefixes = {
            "logo",
            "icon",
            "bg",
            "banner",
            "thumb",
            "image",
            "img",
            "avatar",
            "user",
            "core-js",
            "lodash",
            "bootstrap",
            "react",
            "vue",
            "webpack",
            "swiper",
            "slick",
            "fontawesome",
            "animate",
            "jquery",
            "modernizr",
            "popper",
            "node_modules",
            "bundle",
            "vendor",
            "assets",
            "static",
            "dist",
        }

        self.valid_tlds = {
            "com",
            "id",
            "net",
            "org",
            "biz",
            "info",
            "co",
            "io",
            "ai",
            "me",
            "app",
            "dev",
            "tech",
            "store",
            "online",
            "site",
            "club",
            "shop",
            "xyz",
            "pro",
            "top",
            "vip",
            "global",
            "space",
            "press",
            "group",
            "asia",
            "us",
            "uk",
            "de",
            "fr",
            "it",
            "es",
            "nl",
            "ca",
            "au",
            "sg",
            "my",
            "jp",
            "kr",
            "cn",
            "in",
            "ch",
            "at",
            "se",
            "no",
            "fi",
            "dk",
            "be",
            "pl",
            "cz",
            "gr",
            "pt",
            "nz",
            "mx",
            "br",
            "ar",
            "cl",
            "za",
            "ae",
            "sa",
            "tr",
            "ph",
            "vn",
            "th",
            "tw",
            "hk",
            "edu",
            "gov",
        }

        self.email_regex = re.compile(
            r"\b[A-Za-z0-9][A-Za-z0-9._%+-]{0,62}"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}\b"
        )
        self.invalid_tld_extensions = {
            "png",
            "jpg",
            "jpeg",
            "gif",
            "svg",
            "webp",
            "ico",
            "pdf",
            "mp4",
            "zip",
            "gz",
            "tar",
            "rar",
            "js",
            "css",
            "scss",
            "woff",
            "woff2",
            "ttf",
            "eot",
            "html",
            "htm",
            "php",
            "json",
            "xml",
            "map",
            "md",
            "txt",
            "mp3",
            "wav",
            "avi",
            "mov",
            "exe",
            "dll",
            "dmg",
            "iso",
            "bin",
            "less",
            "ts",
            "jsx",
            "tsx",
            "py",
            "wasm",
            "otf",
            "cjs",
            "mjs",
            "vue",
            "blade",
            "tpl",
            "bak",
            "swp",
            "lock",
            "our",
            "entire",
            "your",
            "ue",
            "we",
            "tf",
            "ws",
            "csbz",
            "what",
            "retention",
            "illegal",
            "user",
            "note",
            "please",
        }

    def validate(self, email: str) -> bool:
        """Validate if given email string is genuine and not false positive."""
        email = email.strip().lower()
        if not email:
            return False

        if not self.email_regex.match(email):
            return False

        try:
            local_part, domain_part = email.split("@", 1)
        except ValueError:
            return False

        if len(local_part) < 2 or len(local_part) > 64:
            return False
        if len(domain_part) < 4 or len(domain_part) > 255:
            return False

        domain_parts = domain_part.split(".")
        if any(len(p) < 2 for p in domain_parts):
            return False

        local_parts = local_part.split(".")
        if any(len(p) < 2 for p in local_parts):
            return False

        tld = domain_parts[-1]
        if tld in self.invalid_tld_extensions or tld.isdigit() or len(tld) < 2:
            return False
        if tld not in self.valid_tlds:
            return False

        # Reject PDF and binary font garbage with no vowels
        if not re.search(r"[aeiouy]", local_part) or not re.search(
            r"[aeiouy]", domain_parts[0]
        ):
            return False

        if domain_part in self.blacklist_domains or any(
            domain_part.endswith("." + d) or d.endswith(domain_part)
            for d in self.blacklist_domains
        ):
            return False

        if email in self.blacklist_emails:
            return False

        if local_part in (
            "noreply",
            "no-reply",
            "donotreply",
            "do-not-reply",
            "mailer-daemon",
        ):
            return False

        if re.search(r"\d+\.\d+(\.\d+)?", local_part) or re.search(
            r"@\d+x\.", email
        ):
            return False

        if any(
            local_part == prefix
            or local_part.startswith(prefix + "@")
            or local_part.startswith(prefix + "-")
            for prefix in self.asset_prefixes
        ):
            return False

        if ".." in local_part or ".." in domain_part:
            return False
        if local_part.startswith((".", "_", "-", "+")) or local_part.endswith(
            (".", "_", "-", "+")
        ):
            return False
        if domain_part.startswith((".", "-")) or domain_part.endswith(
            (".", "-")
        ):
            return False

        if not re.search(r"[A-Za-z]", local_part):
            return False

        return True


class PhoneNumberValidator:
    """High-accuracy Indonesian Phone & WhatsApp number validator."""

    OPERATORS = {
        "0811": "Telkomsel (Halo)",
        "0812": "Telkomsel (SimPATI)",
        "0813": "Telkomsel (SimPATI)",
        "0821": "Telkomsel (SimPATI)",
        "0822": "Telkomsel (Loop/SimPATI)",
        "0823": "Telkomsel (Kartu AS)",
        "0851": "Telkomsel (By.U/AS)",
        "0852": "Telkomsel (Kartu AS)",
        "0853": "Telkomsel (Kartu AS)",
        "0814": "Indosat Ooredoo (Broadband)",
        "0815": "Indosat Ooredoo (Matrix/Mentari)",
        "0816": "Indosat Ooredoo (Matrix/Mentari)",
        "0855": "Indosat Ooredoo (Matrix)",
        "0856": "Indosat Ooredoo (IM3)",
        "0857": "Indosat Ooredoo (IM3)",
        "0858": "Indosat Ooredoo (Mentari)",
        "0817": "XL Axiata",
        "0818": "XL Axiata",
        "0819": "XL Axiata",
        "0859": "XL Axiata",
        "0877": "XL Axiata",
        "0878": "XL Axiata",
        "0831": "Axis",
        "0832": "Axis",
        "0833": "Axis",
        "0838": "Axis",
        "0895": "Tri (3)",
        "0896": "Tri (3)",
        "0897": "Tri (3)",
        "0898": "Tri (3)",
        "0899": "Tri (3)",
        "0881": "Smartfren",
        "0882": "Smartfren",
        "0883": "Smartfren",
        "0884": "Smartfren",
        "0885": "Smartfren",
        "0886": "Smartfren",
        "0887": "Smartfren",
        "0888": "Smartfren",
        "0889": "Smartfren",
    }

    AREA_CODES = {
        "021": {
            "desc": (
                "Telkom PSTN "
                "(Jabodetabek: Jakarta, Bogor, Depok, Tangerang, Bekasi)"
            ),
            "sub_len": (7, 8),
        },
        "022": {
            "desc": "Telkom PSTN (Bandung & Cimahi)",
            "sub_len": (6, 8),
        },
        "0231": {
            "desc": "Telkom PSTN (Cirebon)",
            "sub_len": (6, 7),
        },
        "024": {
            "desc": "Telkom PSTN (Semarang)",
            "sub_len": (6, 8),
        },
        "0251": {
            "desc": "Telkom PSTN (Bogor)",
            "sub_len": (6, 7),
        },
        "0254": {
            "desc": "Telkom PSTN (Serang & Cilegon)",
            "sub_len": (6, 7),
        },
        "0267": {
            "desc": "Telkom PSTN (Karawang)",
            "sub_len": (6, 7),
        },
        "0271": {
            "desc": "Telkom PSTN (Solo / Surakarta)",
            "sub_len": (6, 7),
        },
        "0274": {
            "desc": "Telkom PSTN (Yogyakarta)",
            "sub_len": (6, 7),
        },
        "0281": {
            "desc": "Telkom PSTN (Purwokerto / Banyumas)",
            "sub_len": (6, 7),
        },
        "0283": {
            "desc": "Telkom PSTN (Tegal)",
            "sub_len": (6, 7),
        },
        "0285": {
            "desc": "Telkom PSTN (Pekalongan)",
            "sub_len": (6, 7),
        },
        "0291": {
            "desc": "Telkom PSTN (Kudus)",
            "sub_len": (6, 7),
        },
        "031": {
            "desc": "Telkom PSTN (Surabaya, Sidoarjo, Gresik)",
            "sub_len": (7, 8),
        },
        "0341": {
            "desc": "Telkom PSTN (Malang & Batu)",
            "sub_len": (6, 7),
        },
        "0351": {
            "desc": "Telkom PSTN (Madiun)",
            "sub_len": (6, 7),
        },
        "0361": {
            "desc": "Telkom PSTN (Bali: Denpasar, Badung, Gianyar)",
            "sub_len": (6, 7),
        },
        "0370": {
            "desc": "Telkom PSTN (Mataram / Lombok)",
            "sub_len": (6, 7),
        },
        "0411": {
            "desc": "Telkom PSTN (Makassar)",
            "sub_len": (6, 7),
        },
        "0431": {
            "desc": "Telkom PSTN (Manado)",
            "sub_len": (6, 7),
        },
        "0511": {
            "desc": "Telkom PSTN (Banjarmasin)",
            "sub_len": (6, 7),
        },
        "0541": {
            "desc": "Telkom PSTN (Samarinda)",
            "sub_len": (6, 7),
        },
        "0542": {
            "desc": "Telkom PSTN (Balikpapan)",
            "sub_len": (6, 7),
        },
        "0561": {
            "desc": "Telkom PSTN (Pontianak)",
            "sub_len": (6, 7),
        },
        "061": {
            "desc": "Telkom PSTN (Medan & Deli Serdang)",
            "sub_len": (6, 8),
        },
        "0651": {
            "desc": "Telkom PSTN (Banda Aceh)",
            "sub_len": (6, 7),
        },
        "0711": {
            "desc": "Telkom PSTN (Palembang)",
            "sub_len": (6, 7),
        },
        "0721": {
            "desc": "Telkom PSTN (Bandar Lampung)",
            "sub_len": (6, 7),
        },
        "0741": {
            "desc": "Telkom PSTN (Jambi)",
            "sub_len": (6, 7),
        },
        "0751": {
            "desc": "Telkom PSTN (Padang)",
            "sub_len": (6, 7),
        },
        "0761": {
            "desc": "Telkom PSTN (Pekanbaru)",
            "sub_len": (6, 7),
        },
        "0778": {
            "desc": "Telkom PSTN (Batam)",
            "sub_len": (6, 7),
        },
        "0911": {
            "desc": "Telkom PSTN (Ambon)",
            "sub_len": (6, 7),
        },
        "0951": {
            "desc": "Telkom PSTN (Sorong)",
            "sub_len": (6, 7),
        },
        "0967": {
            "desc": "Telkom PSTN (Jayapura)",
            "sub_len": (6, 7),
        },
    }

    def __init__(
        self,
        custom_blacklist_numbers=None,
        allowed_operators=None,
        include_landline=True,
    ):
        """Initialize validator with operator and PSTN preferences."""
        self.include_landline = include_landline
        self.allowed_operators = (
            set(allowed_operators) if allowed_operators else None
        )

        self.blacklist_numbers = {
            "08123456789",
            "081234567890",
            "0812345678901",
            "08123456789012",
            "08111111111",
            "08222222222",
            "08333333333",
            "08444444444",
            "08555555555",
            "08666666666",
            "08777777777",
            "08888888888",
            "08999999999",
            "08000000000",
            "08120000000",
            "0812345678",
            "08987654321",
            "081298765432",
            "081212341234",
            "08001234567",
            "081212121212",
            "081112223334",
            "081234500000",
            "08001111222",
            "628123456789",
            "6281234567890",
            "628111111111",
            "628000000000",
            "+628123456789",
            "+6281234567890",
            "+628111111111",
            "+628000000000",
        }
        if custom_blacklist_numbers:
            self.blacklist_numbers.update(custom_blacklist_numbers)

        self.mobile_regex = re.compile(
            r"(?<![0-9A-Za-z_\.\-\/])"
            r"(?:(?:\+?62[-.\s]?(?:\(?8[1-9][0-9]{1,2}\)?|8[1-9][0-9]{1,2})"
            r"|\(?08[1-9][0-9]{1,2}\)?)"
            r"[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,5})"
            r"(?![0-9A-Za-z_\.\-\/])"
        )

        self.landline_regex = re.compile(
            r"(?<![0-9A-Za-z_\.\-\/])"
            r"(?:(?:\+?62[-.\s]?(?:\(2[1-9]|3[1-9]|4[1-9]|5[1-9]|6[1-9]|7[1-9]"
            r"|9[1-9]|[0-9]{2,4}\)|(?:21|22|24|31|61|71|41|51|251|274|271|"
            r"341|361|231|254|267|281|283|285|291|351|370|431|541|542|561|"
            r"651|721|741|751|761|778|911|951|967))|\(?0(?:21|22|24|31|61|"
            r"71|41|51|251|274|271|341|361|231|254|267|281|283|285|291|351|"
            r"370|431|541|542|561|651|721|741|751|761|778|911|951|967)\)?)"
            r"[-.\s]?[2-9][0-9]{2,3}[-.\s]?[0-9]{3,4})"
            r"(?![0-9A-Za-z_\.\-\/])"
        )

    def clean_raw_number(self, raw: str) -> str:
        """Strip formatting whitespace and separators from phone string."""
        if not raw:
            return ""
        return re.sub(r"[\s\-\.\(\)\/\\\,]", "", raw.strip())

    def parse_and_validate(self, raw_phone: str) -> dict | None:
        """Parse, validate operator, and return phone metadata dictionary."""
        if not raw_phone:
            return None

        digits = self.clean_raw_number(raw_phone)

        if (
            raw_phone.strip() in self.blacklist_numbers
            or digits in self.blacklist_numbers
        ):
            return None

        if len(digits) < 9 or len(digits) > 15:
            return None

        if len(set(digits)) < 4:
            return None

        if digits.startswith(
            ("899", "199", "2023", "2024", "2025", "2026")
        ) and len(digits) in (13, 14, 15, 16):
            return None

        if digits.startswith("+628"):
            digits = digits[1:]
        elif digits.startswith("08"):
            digits = "62" + digits[1:]

        # === 1. INDONESIAN MOBILE VALIDATION ===
        if digits.startswith("628"):
            if len(digits) < 11 or len(digits) > 14:
                return None

            local_prefix = "0" + digits[2:5]
            operator = self.OPERATORS.get(local_prefix)
            if not operator:
                return None

            if (
                self.allowed_operators
                and operator not in self.allowed_operators
            ):
                return None

            sub_num = digits[5:]
            if len(set(sub_num)) <= 1 or sub_num in (
                "123456",
                "654321",
                "1234567",
                "7654321",
            ):
                return None

            local_digits = "0" + digits[2:]
            if len(local_digits) >= 11:
                national_fmt = (
                    f"{local_digits[:4]}-{local_digits[4:8]}"
                    f"-{local_digits[8:]}"
                )
            else:
                national_fmt = f"{local_digits[:4]}-{local_digits[4:]}"

            return {
                "e164": f"+{digits}",
                "national": national_fmt,
                "clean_digits": digits,
                "operator": operator,
                "type": "Mobile (WhatsApp)",
                "wa_link": f"https://wa.me/{digits}",
            }

        # === 2. INDONESIAN LANDLINE (PSTN) VALIDATION ===
        if self.include_landline:
            landline_digits = digits
            if landline_digits.startswith("+62"):
                landline_digits = "0" + landline_digits[3:]
            elif landline_digits.startswith("62"):
                landline_digits = "0" + landline_digits[2:]

            if landline_digits.startswith("0"):
                matched_area = None
                matched_info = None
                for area in sorted(
                    self.AREA_CODES.keys(), key=len, reverse=True
                ):
                    if landline_digits.startswith(area):
                        matched_area = area
                        matched_info = self.AREA_CODES[area]
                        break

                if matched_area and matched_info:
                    subscriber_part = landline_digits[len(matched_area) :]
                    min_sub, max_sub = matched_info["sub_len"]

                    if not (min_sub <= len(subscriber_part) <= max_sub):
                        return None

                    if subscriber_part[0] in ("0", "1"):
                        return None

                    if len(set(subscriber_part)) <= 1:
                        return None

                    local_landline = landline_digits
                    if len(subscriber_part) > 4:
                        national_fmt = (
                            f"({matched_area}) "
                            f"{subscriber_part[:4]}-{subscriber_part[4:]}"
                        )
                    else:
                        national_fmt = f"({matched_area}) {subscriber_part}"

                    return {
                        "e164": local_landline,
                        "national": national_fmt,
                        "clean_digits": local_landline,
                        "operator": matched_info["desc"],
                        "type": "Landline / Fixed Line",
                        "wa_link": "-",
                    }

        return None


class HttpRequestManager:
    """Manages realistic rotating user agents and request headers."""

    def __init__(self):
        """Initialize list of realistic browser user-agent strings."""
        self.user_agents = [
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) "
                "Gecko/20100101 Firefox/123.0"
            ),
            (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
            ),
            (
                "Mozilla/5.0 (Linux; Android 10; K) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Mobile Safari/537.36"
            ),
        ]

    def get_headers(self) -> dict:
        """Return HTTP headers with randomly chosen user-agent."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive",
        }


class SearchEngineScraper:
    """Discovers target URLs with strict brand and relevance validation."""

    def __init__(self):
        """Initialize HTTP manager and relevance validator."""
        self.http_manager = HttpRequestManager()
        self.relevance_val = CompanyRelevanceValidator()

    def generate_company_domains(self, company_name: str) -> list:
        """Generate candidate website URLs from company brand tokens."""
        brand_tokens = self.relevance_val.get_brand_tokens(company_name)
        if not brand_tokens:
            return []

        combos = []
        if len(brand_tokens) >= 2:
            combos.append("".join(brand_tokens))
            combos.append("-".join(brand_tokens))
            if (
                brand_tokens[-1] in ("indonesia", "group", "company")
                and len(brand_tokens) >= 3
            ):
                combos.append("".join(brand_tokens[:-1]))
            elif len(brand_tokens) == 2 and brand_tokens[-1] in (
                "indonesia",
                "group",
                "company",
            ):
                combos.append(brand_tokens[0])
            elif len(brand_tokens) > 2:
                combos.append("".join(brand_tokens[:2]))
                combos.append(brand_tokens[0] + brand_tokens[-1])
        else:
            combos.append(brand_tokens[0])

        tlds = [".co.id", ".com", ".id", ".net", ".co"]
        candidates = []
        for c in combos:
            for tld in tlds:
                candidates.append(f"https://www.{c}{tld}")
                candidates.append(f"https://{c}{tld}")
        return list(dict.fromkeys(candidates))

    async def probe_company_domains(
        self, candidates: list, company_name: str
    ) -> list:
        """Probe candidate domains to find live company website."""
        connector = aiohttp.TCPConnector(
            resolver=aiohttp.ThreadedResolver(), ssl=False
        )
        timeout = aiohttp.ClientTimeout(total=4, connect=2)
        valid = []
        headers = self.http_manager.get_headers()
        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout, headers=headers
        ) as session:
            for url in candidates[:16]:
                try:
                    async with session.get(
                        url, allow_redirects=True
                    ) as response:
                        if response.status == 200:
                            final_url = str(response.url).rstrip("/")
                            if not self.relevance_val.is_url_strictly_blocked(
                                final_url
                            ):
                                domain = urllib.parse.urlparse(
                                    final_url
                                ).netloc.lower()
                                html = await response.text(errors="ignore")
                                soup = BeautifulSoup(html, "html.parser")
                                title = soup.title.string if soup.title else ""
                                if self.relevance_val.is_page_relevant(
                                    html, str(title), company_name, domain
                                ):
                                    valid.append(final_url)
                except Exception:
                    pass
        return list(dict.fromkeys(valid))

    async def search_company(self, company_name: str) -> list:
        """Execute company discovery with probe and search fallbacks."""
        # 1. Probe direct domain candidates
        candidates = self.generate_company_domains(company_name)
        probed_urls = await self.probe_company_domains(
            candidates, company_name
        )
        if probed_urls:
            return probed_urls

        # 2. Search query fallback
        query = f'"{company_name}" marmer OR granit OR kaca OR batu'
        search_res = await self.search(query, num_results=10)

        verified = []
        for url in search_res:
            if not self.relevance_val.is_url_strictly_blocked(url):
                domain = urllib.parse.urlparse(url).netloc.lower()
                if self.relevance_val.is_domain_brand_match(
                    domain, company_name
                ):
                    verified.append(url)

        return verified[:3]

    async def search(self, query: str, num_results: int = 200) -> list:
        """Search query across Bing, Yahoo, and DuckDuckGo engines."""
        pages_to_request = max(1, (num_results // 10) + 1)
        tasks = []
        for p in range(min(5, pages_to_request)):
            first_idx = (p * 10) + 1
            tasks.append(self._search_bing(query, first_idx))
        for p in range(min(5, pages_to_request)):
            first_idx = (p * 10) + 1
            tasks.append(self._search_yahoo(query, first_idx))
        tasks.append(self._search_duckduckgo(query))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        urls = set()
        for res in results:
            if isinstance(res, list):
                for url in res:
                    try:
                        parsed = urllib.parse.urlparse(url)
                        clean_url = (
                            f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        )
                        if (
                            parsed.netloc
                            and not self.relevance_val.is_url_strictly_blocked(
                                clean_url
                            )
                        ):
                            urls.add(clean_url.rstrip("/"))
                    except Exception:
                        urls.add(url)

        filtered_urls = [
            u
            for u in urls
            if not self.relevance_val.is_url_strictly_blocked(u)
        ]
        return list(set(filtered_urls))[:num_results]

    def _decode_bing_u(self, u_param: str) -> str:
        """Decode base64 encoded URL parameter in Bing search results."""
        try:
            raw = u_param[2:] if u_param.startswith("a1") else u_param
            raw += "=" * (-len(raw) % 4)
            return base64.urlsafe_b64decode(raw).decode(
                "utf-8", errors="ignore"
            )
        except Exception:
            return ""

    async def _search_bing(self, query: str, first: int) -> list:
        """Fetch search result links from Bing."""
        found_urls = []
        encoded_query = urllib.parse.quote_plus(query)
        url = (
            f"https://www.bing.com/search?q={encoded_query}&first={first}"
            "&setmkt=id-ID&setlang=id&cc=ID"
        )
        try:
            headers = self.http_manager.get_headers()
            connector = aiohttp.TCPConnector(
                ssl=False, resolver=aiohttp.ThreadedResolver()
            )
            async with aiohttp.ClientSession(
                headers=headers, connector=connector
            ) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        for a in soup.select("li.b_algo h2 a, h2 a"):
                            href = a.get("href", "")
                            if "/ck/a?!" in href:
                                parsed = urllib.parse.urlparse(href)
                                qs = urllib.parse.parse_qs(parsed.query)
                                if "u" in qs:
                                    target = self._decode_bing_u(qs["u"][0])
                                    if target.startswith(
                                        (
                                            "http://",
                                            "https://",
                                        )
                                    ) and not (
                                        self.relevance_val.is_url_strictly_blocked(
                                            target
                                        )
                                    ):
                                        found_urls.append(target)
                            elif href.startswith(
                                (
                                    "http://",
                                    "https://",
                                )
                            ) and not (
                                self.relevance_val.is_url_strictly_blocked(
                                    href
                                )
                            ):
                                found_urls.append(href)
        except Exception:
            pass
        return found_urls

    async def _search_yahoo(self, query: str, first: int) -> list:
        """Fetch search result links from Yahoo."""
        found_urls = []
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://search.yahoo.com/search?p={encoded_query}&b={first}"
        try:
            headers = self.http_manager.get_headers()
            connector = aiohttp.TCPConnector(
                ssl=False, resolver=aiohttp.ThreadedResolver()
            )
            async with aiohttp.ClientSession(
                headers=headers, connector=connector
            ) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            if "/RU=" in href:
                                try:
                                    target = urllib.parse.unquote(
                                        href.split("/RU=")[1].split("/RK=")[0]
                                    )
                                    if target.startswith(
                                        (
                                            "http://",
                                            "https://",
                                        )
                                    ) and not (
                                        self.relevance_val.is_url_strictly_blocked(
                                            target
                                        )
                                    ):
                                        found_urls.append(target)
                                except Exception:
                                    pass
                            elif href.startswith(
                                (
                                    "http://",
                                    "https://",
                                )
                            ) and not (
                                self.relevance_val.is_url_strictly_blocked(
                                    href
                                )
                            ):
                                found_urls.append(href)
        except Exception:
            pass
        return found_urls

    async def _search_duckduckgo(self, query: str) -> list:
        """Fetch search result links from DuckDuckGo HTML endpoint."""
        found_urls = []
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        try:
            headers = self.http_manager.get_headers()
            connector = aiohttp.TCPConnector(
                ssl=False, resolver=aiohttp.ThreadedResolver()
            )
            async with aiohttp.ClientSession(
                headers=headers, connector=connector
            ) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        for a in soup.find_all("a", href=True):
                            href = a["href"]
                            if "/l/?" in href or "uddg=" in href:
                                parsed = urllib.parse.urlparse(href)
                                qs = urllib.parse.parse_qs(parsed.query)
                                if "uddg" in qs:
                                    ext_url = qs["uddg"][0]
                                    if not (
                                        self.relevance_val.is_url_strictly_blocked(
                                            ext_url
                                        )
                                    ):
                                        found_urls.append(ext_url)
                            elif href.startswith(
                                (
                                    "http://",
                                    "https://",
                                )
                            ) and not (
                                self.relevance_val.is_url_strictly_blocked(
                                    href
                                )
                            ):
                                found_urls.append(href)
        except Exception:
            pass
        return found_urls


class AsyncDualScraper:
    """Asynchronous dual crawler for simultaneous Email & Phone extraction."""

    def __init__(
        self,
        start_urls,
        max_depth=1,
        max_pages=100,
        concurrent_connections=15,
        internal_only=True,
        deobfuscate=True,
        scrape_emails=True,
        scrape_phones=True,
        email_validator=None,
        phone_validator=None,
        update_callback=None,
    ):
        """Initialize the crawler with validation and concurrency limits."""
        self.start_urls = [
            self._normalize_url(url) for url in start_urls if url.strip()
        ]
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.concurrent_connections = concurrent_connections
        self.internal_only = internal_only
        self.deobfuscate = deobfuscate
        self.scrape_emails = scrape_emails
        self.scrape_phones = scrape_phones

        self.email_validator = email_validator or EmailValidator()
        self.phone_validator = phone_validator or PhoneNumberValidator()
        self.update_callback = update_callback

        self.scraped_emails = {}  # email -> set(source_urls)
        self.scraped_numbers = {}  # e164 -> dict(meta, sources: set)
        self.scraped_leads = {}  # url -> dict(domain, emails, phones)
        self.visited_urls = set()
        self.allowed_domains = {
            self._get_domain(url)
            for url in self.start_urls
            if self._get_domain(url)
        }

        self.crawled_count = 0
        self.success_count = 0
        self.error_count = 0
        self.is_running = False
        self.status_log = []

        self.http_manager = HttpRequestManager()
        self.relevance_val = CompanyRelevanceValidator()
        self.session = None
        self.semaphore = None
        self.queue = None

    def _normalize_url(self, url: str) -> str:
        """Prepend https scheme if missing."""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    def _get_domain(self, url: str) -> str:
        """Extract root domain without www prefix."""
        try:
            return (
                urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
            )
        except Exception:
            return ""

    def log(self, message: str):
        """Append log message and call registered update callback."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}"
        self.status_log.append(formatted)
        if self.update_callback:
            self.update_callback(formatted, self)

    async def start(self):
        """Start async crawler with workers up to concurrency limit."""
        self.is_running = True
        targets_info = []
        if self.scrape_emails:
            targets_info.append("Emails")
        if self.scrape_phones:
            targets_info.append("Phone/WA Numbers")
        target_str = " & ".join(targets_info) if targets_info else "Data"

        self.log(
            f"[INFO] Dual Scraper initialized for {target_str} "
            f"with {len(self.start_urls)} target URLs."
        )
        self.log(
            f"[INFO] Settings: Max Depth={self.max_depth}, "
            f"Max Pages={self.max_pages}, "
            f"Max Concurrency={self.concurrent_connections}"
        )

        timeout = aiohttp.ClientTimeout(total=15, connect=5)
        connector = aiohttp.TCPConnector(
            limit=self.concurrent_connections,
            ssl=False,
            resolver=aiohttp.ThreadedResolver(),
            family=0,
        )

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            self.session = session
            self.semaphore = asyncio.Semaphore(self.concurrent_connections)
            self.queue = asyncio.Queue()

            for url in self.start_urls:
                await self.queue.put((url, 0))

            workers = []
            for _ in range(self.concurrent_connections):
                task = asyncio.create_task(self._worker())
                workers.append(task)

            while self.is_running and self.crawled_count < self.max_pages:
                if (
                    self.queue.empty()
                    and self.semaphore._value == self.concurrent_connections
                ):
                    break
                await asyncio.sleep(0.2)

            self.is_running = False
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

            self.log(
                f"[INFO] Crawl completed. Visited {self.crawled_count} pages. "
                f"Emails: {len(self.scraped_emails)} | "
                f"Phone Numbers: {len(self.scraped_numbers)}"
            )

    async def _worker(self):
        """Worker task processing URLs from async queue."""
        while self.is_running:
            try:
                if self.crawled_count >= self.max_pages:
                    break

                try:
                    url, depth = await asyncio.wait_for(
                        self.queue.get(), timeout=0.5
                    )
                except asyncio.TimeoutError:
                    continue

                if (
                    url in self.visited_urls
                    or self.relevance_val.is_url_strictly_blocked(url)
                ):
                    self.queue.task_done()
                    continue

                self.visited_urls.add(url)

                async with self.semaphore:
                    await self._crawl_page(url, depth)

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log(f"[ERROR] Worker error: {e}")

    def _clean_html_for_text(self, html: str) -> tuple:
        """Strip scripts, styles, templates and return text."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(
                [
                    "script",
                    "style",
                    "svg",
                    "noscript",
                    "iframe",
                    "template",
                    "code",
                    "pre",
                ]
            ):
                tag.decompose()
            visible_text = soup.get_text(separator=" ")
            return soup, visible_text
        except Exception:
            return None, html

    async def _crawl_page(self, url: str, depth: int):
        """Fetch page, extract contacts, and discover internal links."""
        self.crawled_count += 1
        self.log(
            f"[CRAWL] [{self.crawled_count}/{self.max_pages}] "
            f"Fetching: {url} (Depth: {depth})"
        )

        headers = self.http_manager.get_headers()
        try:
            async with self.session.get(
                url, headers=headers, timeout=10, allow_redirects=True
            ) as response:
                if url.lower().endswith(
                    (
                        ".pdf",
                        ".doc",
                        ".docx",
                        ".xls",
                        ".xlsx",
                        ".zip",
                        ".rar",
                        ".exe",
                        ".bin",
                    )
                ):
                    return

                content_type = response.headers.get("Content-Type", "").lower()
                if content_type and not any(
                    ct in content_type
                    for ct in [
                        "text/html",
                        "application/xhtml",
                        "text/plain",
                    ]
                ):
                    return

                self.success_count += 1
                try:
                    html = await response.text(errors="ignore")
                except Exception:
                    html = str(await response.read())

                domain = self._get_domain(url)
                soup, visible_text = self._clean_html_for_text(html)

                extracted_emails = []
                extracted_numbers = []

                if self.scrape_emails:
                    extracted_emails = self._extract_emails(
                        soup, visible_text, url
                    )
                if self.scrape_phones:
                    extracted_numbers = self._extract_numbers(
                        soup, visible_text, url
                    )

                if extracted_emails or extracted_numbers:
                    if url not in self.scraped_leads:
                        self.scraped_leads[url] = {
                            "domain": domain,
                            "emails": set(),
                            "phones": set(),
                            "first_seen": datetime.now().strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                        }
                    self.scraped_leads[url]["emails"].update(extracted_emails)
                    self.scraped_leads[url]["phones"].update(
                        [num["e164"] for num in extracted_numbers]
                    )

                    log_details = []
                    if extracted_emails:
                        log_details.append(f"{len(extracted_emails)} emails")
                    if extracted_numbers:
                        log_details.append(f"{len(extracted_numbers)} numbers")
                    self.log(
                        f"[SUCCESS] Extracted {', '.join(log_details)} "
                        f"from {url}"
                    )

                # Follow links ONLY within internal domain
                if depth < self.max_depth:
                    links = self._extract_links(soup, url)
                    for link in links:
                        if (
                            link not in self.visited_urls
                            and not self.relevance_val.is_url_strictly_blocked(
                                link
                            )
                        ):
                            link_domain = self._get_domain(link)
                            if not link_domain:
                                continue

                            # Strict internal domain check
                            if self.internal_only:
                                if any(
                                    link_domain == d
                                    or link_domain.endswith("." + d)
                                    for d in self.allowed_domains
                                ):
                                    await self.queue.put((link, depth + 1))
                            else:
                                await self.queue.put((link, depth + 1))

        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.error_count += 1
            self.log(f"[ERROR] Fetch failed: {url} | Reason: {e}")

    def _extract_emails(
        self, soup, visible_text: str, source_url: str
    ) -> list:
        """Extract and de-obfuscate emails from HTML and text."""
        emails = []

        if soup:
            try:
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.lower().startswith("mailto:"):
                        email = href[7:].split("?")[0].strip()
                        if self.email_validator.validate(email):
                            emails.append(email)
            except Exception:
                pass

        raw_matches = self.email_validator.email_regex.findall(visible_text)
        for email in raw_matches:
            if self.email_validator.validate(email):
                emails.append(email)

        if self.deobfuscate:
            obfuscated_patterns = [
                r"\b[A-Za-z0-9._%+-]+\s*(?:\[at\]|\(at\)|\{at\}|@|_at_)\s*"
                r"[A-Za-z0-9.-]+(?:\s*(?:\[dot\]|\(dot\)|\{dot\}|\.|_dot_)\s*"
                r"[A-Za-z0-9.-]+)+\b"
            ]
            for pattern in obfuscated_patterns:
                obf_matches = re.findall(pattern, visible_text, re.IGNORECASE)
                for obf in obf_matches:
                    cleaned = re.sub(
                        r"\s*(?:\[at\]|\(at\)|\{at\}|_at_)\s*",
                        "@",
                        obf,
                        flags=re.IGNORECASE,
                    )
                    cleaned = re.sub(
                        r"\s*(?:\[dot\]|\(dot\)|\{dot\}|_dot_)\s*",
                        ".",
                        cleaned,
                        flags=re.IGNORECASE,
                    )
                    cleaned = cleaned.replace(" ", "")
                    if self.email_validator.validate(cleaned):
                        emails.append(cleaned)

        unique_emails = list(set(emails))
        for email in unique_emails:
            if email not in self.scraped_emails:
                self.scraped_emails[email] = set()
            self.scraped_emails[email].add(source_url)

        return unique_emails

    def _extract_numbers(
        self, soup, visible_text: str, source_url: str
    ) -> list:
        """Extract and parse Indonesian phone and WhatsApp numbers."""
        extracted = []

        if soup:
            try:
                for a in soup.find_all("a", href=True):
                    href = a["href"].strip()
                    if href.lower().startswith("tel:"):
                        raw_num = href[4:].split("?")[0].strip()
                        meta = self.phone_validator.parse_and_validate(raw_num)
                        if meta:
                            extracted.append(meta)

                    if "wa.me/" in href:
                        match = re.search(
                            r"wa\.me/(?:\+?62|0)?([0-9]{9,14})", href
                        )
                        if match:
                            meta = self.phone_validator.parse_and_validate(
                                "62" + match.group(1).lstrip("0")
                            )
                            if meta:
                                extracted.append(meta)

                    if (
                        "api.whatsapp.com/send" in href
                        or "web.whatsapp.com/send" in href
                    ):
                        parsed_wa = urllib.parse.urlparse(href)
                        qs = urllib.parse.parse_qs(parsed_wa.query)
                        if "phone" in qs:
                            raw_wa = qs["phone"][0]
                            meta = self.phone_validator.parse_and_validate(
                                raw_wa
                            )
                            if meta:
                                extracted.append(meta)

                for tag in soup.find_all(True):
                    for attr in [
                        "data-phone",
                        "data-tel",
                        "data-whatsapp",
                        "data-mobile",
                        "data-number",
                    ]:
                        if tag.has_attr(attr):
                            val = tag[attr]
                            meta = self.phone_validator.parse_and_validate(
                                str(val)
                            )
                            if meta:
                                extracted.append(meta)
            except Exception:
                pass

        mobile_matches = self.phone_validator.mobile_regex.findall(
            visible_text
        )
        for raw in mobile_matches:
            meta = self.phone_validator.parse_and_validate(raw)
            if meta:
                extracted.append(meta)

        if self.phone_validator.include_landline:
            landline_matches = self.phone_validator.landline_regex.findall(
                visible_text
            )
            for raw in landline_matches:
                meta = self.phone_validator.parse_and_validate(raw)
                if meta:
                    extracted.append(meta)

        if self.deobfuscate:
            obf_patterns = [
                r"(?:(?:\+?62|0)8[0-9]{2}\s*"
                r"(?:\[|\(|\{)?(?:spasi|strip|dash|titik|\-|\.|\s)"
                r"(?:\]|\)|\})?\s*[0-9]{3,4}\s*(?:\[|\(|\{)?"
                r"(?:spasi|strip|dash|titik|\-|\.|\s)(?:\]|\)|\})?\s*"
                r"[0-9]{3,5})"
            ]
            for pat in obf_patterns:
                obf_matches = re.findall(pat, visible_text, re.IGNORECASE)
                for obf in obf_matches:
                    cleaned = re.sub(
                        r"\[|\(|\{|\}|\]|spasi|strip|dash|titik",
                        "",
                        obf,
                        flags=re.IGNORECASE,
                    )
                    cleaned = re.sub(r"[\s\-\.]", "", cleaned)
                    meta = self.phone_validator.parse_and_validate(cleaned)
                    if meta:
                        extracted.append(meta)

        unique_extracted = []
        seen_on_page = set()
        for item in extracted:
            e164 = item["e164"]
            if e164 not in self.scraped_numbers:
                self.scraped_numbers[e164] = {
                    "e164": item["e164"],
                    "national": item["national"],
                    "clean_digits": item["clean_digits"],
                    "operator": item["operator"],
                    "type": item["type"],
                    "wa_link": item["wa_link"],
                    "sources": set(),
                }
            self.scraped_numbers[e164]["sources"].add(source_url)
            if e164 not in seen_on_page:
                seen_on_page.add(e164)
                unique_extracted.append(item)

        return unique_extracted

    def _extract_links(self, soup, base_url: str) -> list:
        """Extract and normalize all anchor hyperlinks from HTML soup."""
        links = []
        if not soup:
            return []

        try:
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if not href or href.startswith(
                    (
                        "#",
                        "javascript:",
                        "mailto:",
                        "tel:",
                        "whatsapp:",
                    )
                ):
                    continue
                full_url = urllib.parse.urljoin(base_url, href)
                if not self.relevance_val.is_url_strictly_blocked(full_url):
                    links.append(full_url)
        except Exception:
            pass

        valid_links = []
        for link in set(links):
            try:
                parsed = urllib.parse.urlparse(link)
                if parsed.scheme in ("http", "https"):
                    path = parsed.path.lower()
                    if not any(
                        path.endswith(ext)
                        for ext in [
                            ".png",
                            ".jpg",
                            ".jpeg",
                            ".gif",
                            ".svg",
                            ".webp",
                            ".pdf",
                            ".css",
                            ".js",
                            ".woff",
                            ".woff2",
                            ".ttf",
                            ".mp4",
                            ".zip",
                            ".mp3",
                        ]
                    ):
                        valid_links.append(link)
            except Exception:
                pass

        return valid_links
