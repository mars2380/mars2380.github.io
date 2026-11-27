#!/usr/bin/env python3
"""Scrape JobServe saved searches and build an HTML table report.

Output columns:
- summary
- position
- salary
- location
- time
- employment business
- contact
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List
from urllib.error import URLError
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.request import Request, urlopen

URLS = [
    "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=ACC44A4FF7C56D07",
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
    employment_business: str = ""
    contact: str = ""


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
                job_url = urljoin(self.base_url, href)
                if "/mob/job/" in urlparse(job_url).path:
                    self._current_href = job_url

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


def _html_to_lines(html: str) -> List[str]:
    cleaned = re.sub(r"<script\\b[^>]*>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<style\\b[^>]*>.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", "\n", cleaned)
    cleaned = re.sub(r"\r", "\n", cleaned)
    cleaned = re.sub(r"\n+", "\n", cleaned)
    return [line.strip() for line in cleaned.split("\n") if line.strip()]


def _extract_jobinfo_lines(html: str) -> List[str]:
    # Prefer parsing inside the jobinfo section from job detail pages.
    blocks = re.findall(
        r"<div[^>]*class=[\"'][^\"']*\bjobinfo\b[^\"']*[\"'][^>]*>(.*?)</div>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not blocks:
        return []

    return _html_to_lines("\n".join(blocks))


def _extract_labeled_value(lines: List[str], labels: List[str]) -> str:
    joined = "(?:" + "|".join(labels) + ")"
    label_only_pattern = re.compile(r"^" + joined + r"\s*$", re.IGNORECASE)
    label_with_value_pattern = re.compile(r"^" + joined + r"\s*[:\-]\s*(.+)$", re.IGNORECASE)

    for idx, line in enumerate(lines):
        same_line_match = label_with_value_pattern.match(line)
        if same_line_match:
            same_line_value = same_line_match.group(1).strip()
            if same_line_value:
                return same_line_value

        if not label_only_pattern.match(line):
            continue

        for next_idx in range(idx + 1, min(idx + 6, len(lines))):
            candidate = lines[next_idx].strip()
            if not candidate:
                continue
            if label_only_pattern.match(candidate) or label_with_value_pattern.match(candidate):
                break
            # If next item looks like a field heading (eg "Telephone:") skip it.
            if candidate.endswith(":"):
                break
            return candidate

    return ""


def extract_job_detail_fields(html: str) -> tuple[str, str]:
    # First try values within the jobinfo class section, then fallback to full page text.
    jobinfo_lines = _extract_jobinfo_lines(html)
    lines = jobinfo_lines if jobinfo_lines else _html_to_lines(html)

    employment_business = _extract_labeled_value(lines, [r"Employment\s+Business", r"Employment\s+Agency"])
    contact = _extract_labeled_value(lines, [r"Contact", r"Contact\s+Name"])

    if not employment_business or not contact:
        full_lines = _html_to_lines(html)
        if not employment_business:
            employment_business = _extract_labeled_value(full_lines, [r"Employment\s+Business", r"Employment\s+Agency"])
        if not contact:
            contact = _extract_labeled_value(full_lines, [r"Contact", r"Contact\s+Name"])

    return employment_business, contact


def enrich_jobs_with_details(jobs: List[Job], timeout: int, insecure: bool) -> None:
    job_urls = list(dict.fromkeys(job.job_url for job in jobs))
    if not job_urls:
        return

    def fetch_details(job_url: str) -> tuple[str, str]:
        try:
            detail_html = fetch_html(job_url, timeout=timeout, insecure=insecure)
        except (URLError, TimeoutError, OSError) as exc:
            print(f"Warning: could not fetch job details for {job_url}: {exc}")
            return "", ""
        return extract_job_detail_fields(detail_html)

    detail_cache: dict[str, tuple[str, str]] = {}
    with ThreadPoolExecutor(max_workers=min(4, len(job_urls))) as executor:
        futures = {
            executor.submit(fetch_details, job_url): job_url for job_url in job_urls
        }
        for completed, future in enumerate(as_completed(futures), start=1):
            detail_cache[futures[future]] = future.result()
            if completed % 25 == 0 or completed == len(job_urls):
                print(f"  Job details fetched: {completed}/{len(job_urls)}")

    for job in jobs:
        employment_business, contact = detail_cache[job.job_url]
        job.employment_business = employment_business
        job.contact = contact


def _extract_search_session_id(jobs: Iterable[Job]) -> str:
    for job in jobs:
        parsed = urlparse(job.job_url)
        if parsed.hostname != "www.jobserve.com":
            continue

        session_ids = parse_qs(parsed.query).get("shid", [])
        if session_ids and re.fullmatch(r"[A-Za-z0-9_-]+", session_ids[0]):
            return session_ids[0]

    return ""


def _build_results_page_url(search_url: str, session_id: str, page_number: int) -> str:
    parsed = urlparse(search_url)
    results_path = parsed.path.rstrip("/")
    if not results_path.endswith("/jobsearch/results"):
        raise ValueError(f"Unexpected JobServe results URL: {search_url}")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
        raise ValueError(f"Invalid JobServe search session ID: {session_id}")

    return parsed._replace(
        path=f"{results_path}/{session_id}",
        query=f"page={page_number}",
        fragment="",
    ).geturl()


def scrape_search_with_pagination(
    search_url: str,
    timeout: int,
    delay: float,
    max_pages: int,
    insecure: bool,
) -> List[Job]:
    first_html = fetch_html(search_url, timeout=timeout, insecure=insecure)
    jobs = parse_jobs(first_html, source_url=search_url)
    session_id = _extract_search_session_id(jobs)
    if not session_id:
        if jobs:
            print(
                f"Warning: could not identify the search session for {search_url}; "
                "only the first page was scraped."
            )
        return jobs

    for page_number in range(2, max_pages + 1):
        time.sleep(delay)
        page_url = _build_results_page_url(search_url, session_id, page_number)
        html = fetch_html(page_url, timeout=timeout, insecure=insecure)
        page_jobs = parse_jobs(html, source_url=page_url)
        if not page_jobs:
            break
        jobs.extend(page_jobs)
    else:
        if jobs:
            print(
                f"Warning: reached the {max_pages}-page limit for {search_url}; "
                "additional results may have been omitted."
            )

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
    last_updated = datetime.now().astimezone().isoformat(
        sep=" ", timespec="seconds"
    )
    rows = []
    for job in jobs:
        rows.append(
            "<tr>"
            f"<td>{escape(job.summary)}</td>"
            f"<td><a href=\"{escape(job.job_url)}\" target=\"_blank\" rel=\"noopener noreferrer\">{escape(job.position)}</a></td>"
            f"<td>{escape(job.salary)}</td>"
            f"<td>{escape(job.location)}</td>"
            f"<td>{escape(job.time)}</td>"
            f"<td>{escape(job.employment_business)}</td>"
            f"<td>{escape(job.contact)}</td>"
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
    table {{ border-collapse: collapse; width: 100%; min-width: 1320px; }}
    th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #154c79; color: #fff; position: sticky; top: 0; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    a {{ color: #0b5fff; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>JobServe Results</h1>
  <p>Last updated: {escape(last_updated)}</p>
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
                    <th>employment business</th>
                    <th>contact</th>
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
    failed_searches = 0

    if args.input_file:
        file_path = Path(args.input_file)
        html = file_path.read_text(encoding="utf-8", errors="replace")
        parsed_jobs = parse_jobs(html, "https://www.jobserve.com")
        all_jobs.extend(parsed_jobs)
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
                failed_searches += 1
                print(f"  Failed: {exc}")

        if failed_searches:
            print("One or more searches failed; existing reports were not overwritten.")
            return 1

    unique_jobs = dedupe_jobs(all_jobs)
    enrich_jobs_with_details(unique_jobs, timeout=args.timeout, insecure=args.insecure)

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
