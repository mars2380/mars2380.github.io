import tempfile
import unittest
from pathlib import Path

from jobserve_scraper import parse_jobs, write_html


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


if __name__ == "__main__":
    unittest.main()
