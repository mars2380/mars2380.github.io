#!/usr/bin/env python3
"""Scrape JobServe saved searches and build an HTML table report.

Output columns:
- summary
- position
- salary
- location
- time
"""

from __future__ import annotations

import argparse
import json
import ssl
import time
from dataclasses import dataclass, asdict
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

URLS = [
    "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B",
    "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DC2CD21F55D1F339",
    "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=4D8DA2CE347175ED",
    "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=DE3E429DC7D11447",
    "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=AA6A02598408858D",
    "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=7A69F1D9B674924A",
]

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}


@dataclass
class Job:
    summary: str
    position: str
    salary: str
    job_url: str
    location: str
    time: str


class JobServeParser(HTMLParser):
    """Parse JobServe mobile result pages into Job entries."""

    def __init__(self, base_url: str, page_summary: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.page_summary = page_summary
        self.jobs: List[Job] = []

        self._inside_job_li = False
        self._current_href = ""
        self._current_position = ""
        self._current_time = ""
        self._generic_spans: List[str] = []

        self._current_span_class = ""
        self._capture_span_text = False
        self._span_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag == "li":
            li_id = attrs_dict.get("id", "") or ""
            if li_id.startswith("J"):
                self._inside_job_li = True
                self._current_href = ""
                self._current_position = ""
                self._current_time = ""
                self._generic_spans = []

        if not self._inside_job_li:
            return

        if tag == "a":
            href = attrs_dict.get("href") or ""
            if href:
                self._current_href = urljoin(self.base_url, href)

        if tag == "span":
            self._current_span_class = attrs_dict.get("class") or ""
            self._capture_span_text = True
            self._span_buffer = []

    def handle_data(self, data: str) -> None:
        if self._inside_job_li and self._capture_span_text:
            self._span_buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self._inside_job_li and tag == "span" and self._capture_span_text:
            value = "".join(self._span_buffer).strip()
            if self._current_span_class == "position":
                self._current_position = value
            elif self._current_span_class == "etime":
                self._current_time = value
            else:
                self._generic_spans.append(value)

            self._current_span_class = ""
            self._capture_span_text = False
            self._span_buffer = []

        if self._inside_job_li and tag == "li":
            salary = self._generic_spans[0].strip() if len(self._generic_spans) > 0 else ""
            location = self._generic_spans[1].strip() if len(self._generic_spans) > 1 else ""

            if self._current_position and self._current_href:
                self.jobs.append(
                    Job(
                        summary=self.page_summary,
                        position=self._current_position,
                        salary=salary,
                        job_url=self._current_href,
                        location=location,
                        time=self._current_time,
                    )
                )

            self._inside_job_li = False
            self._current_href = ""
            self._current_position = ""
            self._current_time = ""
            self._generic_spans = []


class ResultsPaginationParser(HTMLParser):
    """Extract pagination URLs from JobServe results pages."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.pages: set[str] = set()
        self._inside_pages_container = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)

        if tag in {"span", "div"}:
            class_value = attrs_dict.get("class") or ""
            class_tokens = set(class_value.split())
            if "pages" in class_tokens:
                self._inside_pages_container = True

        if tag == "a":
            href = attrs_dict.get("href") or ""
            if not href:
                return
            if self._inside_pages_container or "jobsearch/results" in href:
                self.pages.add(urljoin(self.base_url, href))

    def handle_endtag(self, tag: str) -> None:
        if tag in {"span", "div"} and self._inside_pages_container:
            self._inside_pages_container = False


class ResultsSummaryParser(HTMLParser):
    """Extract only span.searchval values from the summary block."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._inside_searchval_span = False
        self._buf: List[str] = []
        self._current_text: List[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "span":
            class_value = attrs_dict.get("class") or ""
            class_tokens = set(class_value.split())
            if "searchval" in class_tokens:
                self._inside_searchval_span = True
                self._current_text = []

    def handle_data(self, data: str) -> None:
        if self._inside_searchval_span:
            self._current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self._inside_searchval_span:
            value = " ".join("".join(self._current_text).split())
            if value:
                self._buf.append(value)
            self._inside_searchval_span = False
            self._current_text = []

    def summary_text(self) -> str:
        return " | ".join(self._buf)


def fetch_html(url: str, timeout: int, insecure: bool = False) -> str:
    req = Request(url=url, headers=REQUEST_HEADERS)
    context = ssl._create_unverified_context() if insecure else None
    with urlopen(req, timeout=timeout, context=context) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_jobs(html: str, source_url: str) -> List[Job]:
    summary = extract_summary(html)
    parser = JobServeParser(base_url=source_url, page_summary=summary)
    parser.feed(html)
    parser.close()
    return parser.jobs


def extract_summary(html: str) -> str:
    parser = ResultsSummaryParser()
    parser.feed(html)
    parser.close()
    return parser.summary_text()


def extract_results_pages(html: str, source_url: str) -> List[str]:
    parser = ResultsPaginationParser(base_url=source_url)
    parser.feed(html)
    parser.close()

    # Keep only results pages for the same saved search id.
    source_savedsearchid = parse_qs(urlparse(source_url).query).get("savedsearchid", [""])[0]
    filtered: List[str] = []
    for page_url in sorted(parser.pages):
        parsed = urlparse(page_url)
        query = parse_qs(parsed.query)
        if "jobsearch/results" not in parsed.path:
            continue
        if query.get("savedsearchid", [""])[0] != source_savedsearchid:
            continue
        filtered.append(page_url)

    return filtered


def scrape_search_with_pagination(
    search_url: str,
    timeout: int,
    delay: float,
    max_pages: int,
    insecure: bool,
) -> List[Job]:
    visited: set[str] = set()
    to_visit: List[str] = [search_url]
    jobs: List[Job] = []

    while to_visit and len(visited) < max_pages:
        page_url = to_visit.pop(0)
        if page_url in visited:
            continue
        visited.add(page_url)

        html = fetch_html(page_url, timeout=timeout, insecure=insecure)
        page_jobs = parse_jobs(html, source_url=page_url)
        jobs.extend(page_jobs)

        discovered_pages = extract_results_pages(html, source_url=search_url)
        for discovered in discovered_pages:
            if discovered not in visited and discovered not in to_visit:
                to_visit.append(discovered)

        time.sleep(delay)

    return jobs


def dedupe_jobs(jobs: Iterable[Job]) -> List[Job]:
    seen = set()
    unique: List[Job] = []
    for job in jobs:
        key = job.job_url
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)
    return unique


def write_json(path: Path, jobs: List[Job]) -> None:
    data = [asdict(job) for job in jobs]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def write_html(path: Path, jobs: List[Job]) -> None:
    rows = []
    for job in jobs:
        rows.append(
            "<tr>"
            f"<td>{escape(job.summary)}</td>"
            f"<td><a href=\"{escape(job.job_url)}\" target=\"_blank\" rel=\"noopener noreferrer\">{escape(job.position)}</a></td>"
            f"<td>{escape(job.salary)}</td>"
            f"<td>{escape(job.location)}</td>"
            f"<td>{escape(job.time)}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>JobServe Scrape Results</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      margin: 24px;
      background: #f7f7f9;
      color: #222;
    }}
    h1 {{ margin: 0 0 12px; }}
    p {{ margin: 0 0 18px; }}
    .table-wrap {{ overflow-x: auto; background: #fff; border: 1px solid #ddd; }}
    table {{ border-collapse: collapse; width: 100%; min-width: 1080px; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #154c79; color: #fff; position: sticky; top: 0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0b5fff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>JobServe Results</h1>
  <p>Total jobs: {len(jobs)}</p>
  <div class=\"table-wrap\">
    <table>
      <thead>
        <tr>
                    <th>summary</th>
          <th>position</th>
          <th>salary</th>
          <th>location</th>
          <th>time</th>
        </tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape JobServe saved searches")
    parser.add_argument(
        "--output-html",
        default="jobs_table.html",
        help="HTML output file (default: jobs_table.html)",
    )
    parser.add_argument(
        "--output-json",
        default="jobs_data.json",
        help="JSON output file (default: jobs_data.json)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="HTTP timeout in seconds (default: 30)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.8,
        help="Delay between URL fetches in seconds (default: 0.8)",
    )
    parser.add_argument(
        "--input-file",
        help="Optional local HTML file for offline parsing",
    )
    parser.add_argument(
        "--max-pages-per-search",
        type=int,
        default=20,
        help="Safety cap for result pages crawled per saved search (default: 20)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification for HTTP requests",
    )
    args = parser.parse_args()

    all_jobs: List[Job] = []

    if args.input_file:
        file_path = Path(args.input_file)
        html = file_path.read_text(encoding="utf-8", errors="replace")
        all_jobs.extend(parse_jobs(html, "https://www.jobserve.com"))
    else:
        for url in URLS:
            print(f"Fetching: {url}")
            try:
                jobs = scrape_search_with_pagination(
                    search_url=url,
                    timeout=args.timeout,
                    delay=args.delay,
                    max_pages=args.max_pages_per_search,
                    insecure=args.insecure,
                )
                print(f"  Parsed jobs (all pages): {len(jobs)}")
                all_jobs.extend(jobs)
            except Exception as exc:
                print(f"  Failed: {exc}")

    unique_jobs = dedupe_jobs(all_jobs)

    output_html_path = Path(args.output_html)
    output_json_path = Path(args.output_json)
    write_html(output_html_path, unique_jobs)
    write_json(output_json_path, unique_jobs)

    print(f"Done. Wrote {len(unique_jobs)} jobs")
    print(f"HTML: {output_html_path.resolve()}")
    print(f"JSON: {output_json_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
