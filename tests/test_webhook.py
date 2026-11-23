"""The real notifier signs, the real receiver checks: both sides must agree."""
import json
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from collector.notify import (
    SENT_COLUMNS,
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    WebhookNotifier,
    configured_notifiers,
    pending_alerts,
    send_alerts,
)
from demo.receiver import create_app

SECRET = "dummy-secret-change-me"
NOW = 1_794_474_600  # 2026-11-12 09:10 UTC as Unix seconds
EVENT = {"alert_id": "station:142:offline:2026-11-12T08:30Z:started", "subject": "142"}


def signed_message(make_client, signed_at=NOW, secret=SECRET, event=EVENT):
    """Send through the real WebhookNotifier and capture what went over the wire."""
    client, adapter, sleeps = make_client([200])
    notifier = WebhookNotifier(client, "https://receiver.example/events", secret, clock=lambda: signed_at)
    notifier.send("Station 142 offline since 09:30", event)
    request = adapter.calls[0]
    headers = {k: request.headers[k] for k in ("Content-Type", TIMESTAMP_HEADER, SIGNATURE_HEADER)}
    return request.body, headers


@pytest.fixture
def receiver():
    return TestClient(create_app(SECRET, clock=lambda: NOW))


def deliver(receiver, body, headers):
    return receiver.post("/events", content=body, headers=headers)


def test_valid_message_is_accepted(make_client, receiver):
    body, headers = signed_message(make_client)

    response = deliver(receiver, body, headers)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
    assert headers[SIGNATURE_HEADER].startswith("sha256=") and len(headers[SIGNATURE_HEADER]) == 7 + 64


def test_same_message_twice_is_handled_once(make_client, receiver):
    body, headers = signed_message(make_client)

    deliver(receiver, body, headers)
    second = deliver(receiver, body, headers)

    assert second.status_code == 200
    assert second.json() == {"status": "duplicate"}


def test_tampered_body_is_rejected(make_client, receiver):
    body, headers = signed_message(make_client)
    tampered = body.replace(b"142", b"143")

    assert deliver(receiver, tampered, headers).status_code == 401


def test_wrong_secret_is_rejected(make_client, receiver):
    body, headers = signed_message(make_client, secret="someone-elses-secret")

    assert deliver(receiver, body, headers).status_code == 401


@pytest.mark.parametrize(
    "seconds_off, expected",
    [(-299, 200), (-301, 401), (301, 401)],  # inside the window, stale, from the future
)
def test_timestamp_window(make_client, receiver, seconds_off, expected):
    body, headers = signed_message(make_client, signed_at=NOW + seconds_off)

    assert deliver(receiver, body, headers).status_code == expected


def test_old_message_with_a_fresh_timestamp_is_rejected(make_client, receiver):
    # A replay attacker's trick: keep the captured body and signature, update the time.
    body, headers = signed_message(make_client, signed_at=NOW - 3600)
    headers[TIMESTAMP_HEADER] = str(NOW)

    assert deliver(receiver, body, headers).status_code == 401


def test_missing_headers_and_missing_secret_are_rejected(make_client):
    body, headers = signed_message(make_client)

    unsigned = {"Content-Type": "application/json"}
    assert deliver(TestClient(create_app(SECRET, clock=lambda: NOW)), body, unsigned).status_code == 401
    no_secret = TestClient(create_app("", clock=lambda: NOW))
    assert deliver(no_secret, body, headers).status_code == 401


def test_rejection_does_not_tell_the_caller_why(make_client, receiver):
    body, headers = signed_message(make_client, signed_at=NOW - 3600)

    assert deliver(receiver, body, headers).json() == {"detail": "invalid signature"}


def test_webhook_is_on_only_with_url_and_secret():
    on = {"WEBHOOK_URL": "https://receiver.example/events", "WEBHOOK_SECRET": SECRET}

    assert [n.name for n in configured_notifiers(None, env=on)] == ["webhook"]
    assert configured_notifiers(None, env={"WEBHOOK_URL": on["WEBHOOK_URL"]}) == []


def test_alert_fields_travel_in_the_body(make_client):
    client, adapter, sleeps = make_client([200])
    now = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
    events = pd.DataFrame(
        [{"scope": "station", "subject": "142", "state": "offline",
          "started_at": now - timedelta(minutes=30), "ended_at": None, "ended_by": None}]
    )
    notifier = WebhookNotifier(client, "https://receiver.example/events", SECRET, clock=lambda: NOW)

    send_alerts(pending_alerts(events, now), [notifier], pd.DataFrame(columns=SENT_COLUMNS), now)

    sent = json.loads(adapter.calls[0].body)
    assert sent["alert_id"] == "station:142:offline:2026-11-12T08:30Z:started"
    assert sent["kind"] == "started" and sent["text"] == "Station 142 offline since 09:30"
