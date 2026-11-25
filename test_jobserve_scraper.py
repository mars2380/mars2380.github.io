import unittest

from jobserve_scraper import parse_jobs


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


if __name__ == "__main__":
    unittest.main()
