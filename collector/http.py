"""The one HTTP client: timeouts, retries, backoff."""
import logging
import random
import time

import requests

from collector.config import USER_AGENT

log = logging.getLogger(__name__)

# Statuses where waiting can help. Any other 4xx means our request is wrong,
# and sending it again gets the same answer.
RETRY_STATUSES = {429, 500, 502, 503, 504}


class HttpError(Exception):
    def __init__(self, url, status, attempts):
        super().__init__(f"GET {url} failed after {attempts} attempt(s), last status {status}")
        self.url = url
        self.status = status
        self.attempts = attempts


class HttpClient:
    def __init__(
        self,
        session=None,
        timeout=(5, 20),
        max_attempts=5,
        base_delay=1.0,
        max_delay=30.0,
        sleep=time.sleep,
    ):
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        # (connect, read): 5 s to reach the server, 20 s of silence while it answers.
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.sleep = sleep

    def get_json(self, url, params=None):
        for attempt in range(1, self.max_attempts + 1):
            started = time.monotonic()
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                status = response.status_code
            except (requests.Timeout, requests.ConnectionError) as exc:
                response = None
                status = type(exc).__name__
            log.info(
                "GET %s status=%s duration=%.2fs attempt=%d",
                url, status, time.monotonic() - started, attempt,
            )

            if response is not None and response.ok:
                return response.json()
            if response is not None and status not in RETRY_STATUSES:
                raise HttpError(url, status, attempt)
            if attempt == self.max_attempts:
                break

            wait = self._wait_seconds(attempt, response)
            if wait is None:
                break
            self.sleep(wait)

        raise HttpError(url, status, attempt)

    def _wait_seconds(self, attempt, response):
        retry_after = response.headers.get("Retry-After") if response is not None else None
        # TODO: Retry-After may also be an HTTP date. Neither feed has sent one so far.
        if retry_after is not None and retry_after.strip().isdigit():
            seconds = int(retry_after)
            # Longer than we are willing to wait inside one run: give up, the next run retries.
            return seconds if seconds <= self.max_delay else None

        ceiling = min(self.max_delay, self.base_delay * 2 ** (attempt - 1))
        return random.uniform(0, ceiling)
