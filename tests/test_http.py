import pytest
import requests

from collector.config import USER_AGENT
from collector.http import HttpError

URL = "https://feed.example/station_status"


def test_returns_json_on_first_success(make_client):
    client, adapter, sleeps = make_client([200])

    assert client.get_json(URL) == {"ok": True}
    assert len(adapter.calls) == 1
    assert sleeps == []


def test_retries_503_then_succeeds(make_client):
    client, adapter, sleeps = make_client([503, 503, 200])

    assert client.get_json(URL) == {"ok": True}
    assert len(adapter.calls) == 3
    assert len(sleeps) == 2


def test_retries_after_a_timeout(make_client):
    client, adapter, sleeps = make_client([requests.Timeout(), 200])

    assert client.get_json(URL) == {"ok": True}
    assert len(adapter.calls) == 2


def test_404_is_not_retried(make_client):
    client, adapter, sleeps = make_client([404])

    with pytest.raises(HttpError) as error:
        client.get_json(URL)

    assert error.value.status == 404
    assert len(adapter.calls) == 1
    assert sleeps == []


def test_gives_up_after_max_attempts(make_client):
    client, adapter, sleeps = make_client([503] * 5)

    with pytest.raises(HttpError) as error:
        client.get_json(URL)

    assert error.value.attempts == 5
    assert len(sleeps) == 4


def test_backoff_waits_stay_between_half_and_full_ceiling(make_client):
    client, adapter, sleeps = make_client([503] * 5)

    with pytest.raises(HttpError):
        client.get_json(URL)

    # Jitter makes each wait random, but always between half and all of 1, 2, 4, 8 seconds.
    for wait, ceiling in zip(sleeps, [1, 2, 4, 8]):
        assert ceiling / 2 <= wait <= ceiling


def test_each_wait_is_at_least_as_long_as_the_previous(make_client):
    client, adapter, sleeps = make_client([503] * 5)

    with pytest.raises(HttpError):
        client.get_json(URL)

    for earlier, later in zip(sleeps, sleeps[1:]):
        assert later >= earlier


def test_retry_after_is_obeyed(make_client):
    client, adapter, sleeps = make_client([(429, {"Retry-After": "7"}), 200])

    assert client.get_json(URL) == {"ok": True}
    assert sleeps == [7]


def test_retry_after_longer_than_the_cap_gives_up(make_client):
    client, adapter, sleeps = make_client([(503, {"Retry-After": "3600"})])

    with pytest.raises(HttpError):
        client.get_json(URL)

    assert len(adapter.calls) == 1
    assert sleeps == []


def test_sends_our_user_agent(make_client):
    client, adapter, sleeps = make_client([200])

    client.get_json(URL)

    assert adapter.calls[0].headers["User-Agent"] == USER_AGENT
