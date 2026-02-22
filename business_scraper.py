"""Professional and configurable business listing scraper.

Features:
- Robust HTTP requests with retry strategy
- Configurable CSS selectors for broad website compatibility
- CSV and JSON output support
- Clean logging and clear English error messages
- Command-line interface for easy automation
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


@dataclass
class BusinessRecord:
    """Data model for one scraped business entry."""

    name: str
    email: str


class BusinessScraper:
    """Scrapes business cards from a target page using configurable selectors."""

    def __init__(
        self,
        timeout: int = 15,
        user_agent: str = DEFAULT_USER_AGENT,
        max_retries: int = 3,
        backoff_factor: float = 0.7,
    ) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

        retry_policy = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def fetch_html(self, url: str) -> str:
        """Fetch raw HTML from URL with robust error handling."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            raise RuntimeError(f"Failed to fetch URL: {url}") from exc

    def parse(
        self,
        html: str,
        card_selector: str,
        name_selector: str,
        email_selector: str,
    ) -> List[BusinessRecord]:
        """Parse business records from HTML using CSS selectors."""
        soup = BeautifulSoup(html, "html.parser")
        records: List[BusinessRecord] = []

        for card in soup.select(card_selector):
            name_element = card.select_one(name_selector)
            email_element = card.select_one(email_selector)

            name = name_element.get_text(strip=True) if name_element else "N/A"
            email = email_element.get_text(strip=True) if email_element else "N/A"

            records.append(BusinessRecord(name=name, email=email))

        return records


def write_csv(records: Sequence[BusinessRecord], output_path: Path) -> None:
    """Write records to CSV."""
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Email"])
        writer.writerows([[item.name, item.email] for item in records])


def write_json(records: Sequence[BusinessRecord], output_path: Path) -> None:
    """Write records to JSON."""
    payload = [{"name": item.name, "email": item.email} for item in records]
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def validate_output_path(path: str, output_format: str) -> Path:
    """Ensure output file has expected extension and parent directory exists."""
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    expected_suffix = f".{output_format}"
    if output_path.suffix.lower() != expected_suffix:
        output_path = output_path.with_suffix(expected_suffix)

    return output_path


def configure_logger(verbose: bool) -> None:
    """Configure logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    """Build command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Scrape business name and email data from a web page."
    )
    parser.add_argument("url", help="Target URL to scrape")
    parser.add_argument(
        "--output",
        default="marketing_list.csv",
        help="Output file path (default: marketing_list.csv)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--card-selector",
        default="div.business-card",
        help="CSS selector for each business card (default: div.business-card)",
    )
    parser.add_argument(
        "--name-selector",
        default="h2",
        help="CSS selector for business name in card (default: h2)",
    )
    parser.add_argument(
        "--email-selector",
        default="span.email",
        help="CSS selector for email in card (default: span.email)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="HTTP timeout in seconds (default: 15)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logs",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Run scraping workflow."""
    configure_logger(args.verbose)
    logging.info("Starting scraping job for: %s", args.url)

    scraper = BusinessScraper(timeout=args.timeout)
    try:
        html = scraper.fetch_html(args.url)
    except RuntimeError as exc:
        logging.error("%s", exc)
        return 1

    records = scraper.parse(
        html=html,
        card_selector=args.card_selector,
        name_selector=args.name_selector,
        email_selector=args.email_selector,
    )

    if not records:
        logging.warning("No matching records found. Check selectors and target HTML structure.")
        return 0

    output_path = validate_output_path(args.output, args.format)
    if args.format == "csv":
        write_csv(records, output_path)
    else:
        write_json(records, output_path)

    logging.info("Scraping completed successfully. %d records saved to %s", len(records), output_path)
    return 0


def main() -> None:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
