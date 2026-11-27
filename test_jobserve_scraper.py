import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jobserve_scraper import parse_jobs, scrape_search_with_pagination, write_html


class JobServeParserTests(unittest.TestCase):
    def test_job_url_uses_job_detail_link_not_results_link(self):
        source_url = (
            "https://www.jobserve.com/gb/en/mob/jobsearch/results/"
            "0939F16F19FE1954F6B4"
        )
        expected_job_url = (
            "https://www.jobserve.com/gb/en/mob/job/"
            "EFC60D4EDCB4138640?shid=0939F16F19FE1954F6B4&page=1"
        )
        html = """
        <ul>
          <li id="J123">
            <a href="/gb/en/mob/job/EFC60D4EDCB4138640?shid=0939F16F19FE1954F6B4&page=1">
              <span class="position">Example role</span>
            </a>
            <a href="/gb/en/mob/jobsearch/results/0939F16F19FE1954F6B4">
              <span>Search results</span>
            </a>
          </li>
        </ul>
        """

        jobs = parse_jobs(html, source_url)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].job_url, expected_job_url)

    def test_generated_html_includes_last_updated_timestamp(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "index.html"
            write_html(output_path, [])

            html = output_path.read_text(encoding="utf-8")

        self.assertRegex(
            html,
            r"<p>Last updated: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}</p>",
        )

    def test_scraper_fetches_pages_from_the_jobserve_search_session(self):
        search_url = (
            "https://www.jobserve.com/gb/en/mob/jobsearch/results"
            "?savedsearchid=SEARCH123"
        )
        first_page = """
        <span class="searchval">DevOps | London</span>
        <li id="JONE">
          <a href="/gb/en/mob/job/ONE?shid=SESSION123&amp;page=1">
            <span class="position">Page one job</span>
          </a>
          <span class="salary">£500</span>
          <span class="location">London</span>
          <span class="etime">1 hour ago</span>
        </li>
        """
        second_page = """
        <span class="searchval">DevOps | London</span>
        <li id="JTWO">
          <a href="/gb/en/mob/job/TWO?shid=SESSION123&amp;page=2">
            <span class="position">Page two job</span>
          </a>
          <span class="salary">£600</span>
          <span class="location">London</span>
          <span class="etime">2 hours ago</span>
        </li>
        """

        with (
            patch(
                "jobserve_scraper.fetch_html",
                side_effect=[first_page, second_page, "<html></html>"],
            ) as fetch_html,
            patch("jobserve_scraper.time.sleep"),
        ):
            jobs = scrape_search_with_pagination(
                search_url=search_url,
                timeout=10,
                delay=0,
                max_pages=4,
                insecure=False,
            )

        self.assertEqual([job.position for job in jobs], ["Page one job", "Page two job"])
        self.assertEqual(
            [call.args[0] for call in fetch_html.call_args_list],
            [
                search_url,
                "https://www.jobserve.com/gb/en/mob/jobsearch/results/SESSION123?page=2",
                "https://www.jobserve.com/gb/en/mob/jobsearch/results/SESSION123?page=3",
            ],
        )


if __name__ == "__main__":
    unittest.main()
