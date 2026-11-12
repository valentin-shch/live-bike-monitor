import pytest
import requests

from collector.http import HttpClient


class FakeAdapter(requests.adapters.BaseAdapter):
    """Plays a script of answers instead of touching the network.

    Each script item is a status code, a (status, headers) pair, bytes (a 200 with that
    body), or an exception to raise.
    """

    def __init__(self, script):
        super().__init__()
        self.script = list(script)
        self.calls = []

    def send(self, request, **kwargs):
        self.calls.append(request)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        body = b'{"ok": true}'
        if isinstance(item, bytes):
            status, headers, body = 200, {}, item
        elif isinstance(item, tuple):
            status, headers = item
        else:
            status, headers = item, {}

        response = requests.Response()
        response.status_code = status
        response.headers.update(headers)
        response._content = body
        response.url = request.url
        response.request = request
        return response

    def close(self):
        pass


@pytest.fixture
def make_client():
    def _make(script):
        adapter = FakeAdapter(script)
        session = requests.Session()
        session.mount("https://", adapter)
        sleeps = []
        client = HttpClient(session=session, sleep=sleeps.append)
        return client, adapter, sleeps

    return _make
