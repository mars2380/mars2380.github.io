import unittest
from unittest.mock import patch

import jobs


class FakeResponse:
    def __init__(self, text):
        self.content = text.encode("utf-8")

    def raise_for_status(self):
        return None


class JobsPageTests(unittest.TestCase):
    @patch("jobs.requests.get")
    def test_page_returns_original_url_when_results_container_missing(self, mock_get):
        mock_get.return_value = FakeResponse("<html><body><h1>Login page</h1></body></html>")

        self.assertEqual(jobs.page("https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B"), [
            "https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B"
        ])

    @patch("jobs.requests.get")
    def test_page_extracts_pagination_links_from_results_container(self, mock_get):
        mock_get.return_value = FakeResponse("""
        <html><body>
          <div id="cnt">
            <span class="pages">
              <a href="/gb/en/mob/jobsearch/results?page=2">2</a>
              <a href="/gb/en/mob/jobsearch/results?page=3">3</a>
            </span>
          </div>
        </body></html>
        """)

        result = jobs.page("https://www.jobserve.com/gb/en/mob/jobsearch/results?savedsearchid=78A9B33B42D9BA8B")

        self.assertIn("https://www.jobserve.com/gb/en/mob/jobsearch/results?page=2", result)
        self.assertIn("https://www.jobserve.com/gb/en/mob/jobsearch/results?page=3", result)


if __name__ == "__main__":
    unittest.main()
