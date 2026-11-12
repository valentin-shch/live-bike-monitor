import pytest
import requests

from collector.http import HttpClient


class FakeAdapter(requests.adapters.BaseAdapter):
    """Plays a script of answers instead of touching the network.

    Each script item is a status code, a (status, headers) pair, or an exception to raise.
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
        status, headers = item if isinstance(item, tuple) else (item, {})

        response = requests.Response()
        response.status_code = status
        response.headers.update(headers)
        response._content = b'{"ok": true}'
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
