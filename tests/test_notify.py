import json
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from collector.http import HttpError
from collector.notify import (
    SENT_COLUMNS,
    SlackNotifier,
    TelegramNotifier,
    configured_notifiers,
    pending_alerts,
    send_alerts,
)

NOW = datetime(2026, 11, 12, 9, 0, tzinfo=timezone.utc)
TOKEN = "123456:dummy-token-for-tests"


def events(*rows):
    return pd.DataFrame(
        [
            {"scope": scope, "subject": subject, "state": state, "started_at": start, "ended_at": end}
            for scope, subject, state, start, end in rows
        ]
    )


def ago(minutes):
    return NOW - timedelta(minutes=minutes)


class FakeNotifier:
    def __init__(self, name="fake", fail_after=None):
        self.name, self.fail_after, self.texts = name, fail_after, []

    def send(self, text, event=None):
        if self.fail_after is not None and len(self.texts) >= self.fail_after:
            raise HttpError("fake channel", 503, 1, method="POST")
        self.texts.append(text)


NO_SENT = pd.DataFrame(columns=SENT_COLUMNS)


# ---------- which channels are on ----------

@pytest.mark.parametrize(
    "env, expected",
    [
        ({}, []),
        ({"TELEGRAM_BOT_TOKEN": TOKEN}, []),  # half configured stays off
        ({"TELEGRAM_BOT_TOKEN": TOKEN, "TELEGRAM_CHAT_ID": "42"}, ["telegram"]),
        ({"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}, []),  # blank lines from .env.example
        ({"SLACK_WEBHOOK_URL": "https://hooks.example/x"}, ["slack"]),
    ],
)
def test_channels_are_off_unless_configured(env, expected):
    assert [n.name for n in configured_notifiers(client=None, env=env)] == expected


# ---------- what the channels send ----------

def test_telegram_posts_the_text_and_never_logs_the_token(make_client, caplog):
    caplog.set_level(logging.INFO)
    client, adapter, sleeps = make_client([200])

    TelegramNotifier(client, TOKEN, "42").send("Station 142 offline since 09:15")

    request = adapter.calls[0]
    assert request.url == f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    assert json.loads(request.body) == {"chat_id": "42", "text": "Station 142 offline since 09:15"}
    assert TOKEN not in caplog.text
    assert "telegram sendMessage" in caplog.text


def test_failed_post_is_not_retried_and_hides_the_url(make_client):
    client, adapter, sleeps = make_client([503])
    secret_url = "https://hooks.example/services/T000/B000/dummysecret"

    with pytest.raises(HttpError) as info:
        SlackNotifier(client, secret_url).send("hello")

    assert len(adapter.calls) == 1 and sleeps == []
    assert "dummysecret" not in str(info.value)


# ---------- from events to alerts ----------

def test_only_recent_alert_worthy_changes_become_alerts():
    alerts = pending_alerts(
        events(
            ("station", "142", "offline", ago(30), None),
            ("station", "7", "empty", ago(30), None),          # empty: site only
            ("station", "366", "retired", ago(30), None),      # retired: not news
            ("station", "12", "offline", ago(600), ago(60)),   # old start, recent end
            ("feed", "freshness", "stale", ago(600), ago(500)),  # all old
        ),
        NOW,
    )

    # Oldest change first: 12 came back at 08:00, 142 went offline at 08:30.
    assert alerts["alert_id"].tolist() == [
        "station:12:offline:2026-11-11T23:00Z:ended",
        "station:142:offline:2026-11-12T08:30Z:started",
    ]


def test_messages_use_madrid_time():
    alerts = pending_alerts(events(("station", "12", "offline", ago(600), ago(60))), NOW)
    notifier = FakeNotifier()

    send_alerts(alerts, [notifier], NO_SENT, NOW)

    # 23:00 UTC is 00:00 in Madrid in November (UTC+1); 08:00 UTC is 09:00.
    assert notifier.texts == ["Station 12 back online at 09:00 (offline since 00:00)"]


# ---------- once per channel ----------

def test_second_run_sends_nothing_new():
    alerts = pending_alerts(events(("station", "142", "offline", ago(30), None)), NOW)
    notifier = FakeNotifier()

    first = send_alerts(alerts, [notifier], NO_SENT, NOW)
    second = send_alerts(alerts, [notifier], first, NOW + timedelta(minutes=15))

    assert len(notifier.texts) == 1
    assert second.empty


def test_each_channel_keeps_its_own_receipts():
    alerts = pending_alerts(events(("station", "142", "offline", ago(30), None)), NOW)
    telegram, slack = FakeNotifier("telegram"), FakeNotifier("slack")
    sent_by_telegram_only = send_alerts(alerts, [telegram], NO_SENT, NOW)

    send_alerts(alerts, [telegram, slack], sent_by_telegram_only, NOW)

    assert len(telegram.texts) == 1 and len(slack.texts) == 1


def test_failed_send_is_not_recorded_so_the_next_run_retries():
    alerts = pending_alerts(
        events(("station", "1", "offline", ago(45), None), ("station", "2", "offline", ago(30), None)),
        NOW,
    )

    first = send_alerts(alerts, [FakeNotifier(fail_after=1)], NO_SENT, NOW)
    retry = FakeNotifier()
    send_alerts(alerts, [retry], first.assign(channel="fake"), NOW)

    assert first["alert_id"].tolist() == ["station:1:offline:2026-11-12T08:15Z:started"]
    assert retry.texts == ["Station 2 offline since 09:30"]


def test_flood_becomes_nine_messages_and_one_summary():
    rows = [("station", str(i), "offline", ago(30), None) for i in range(25)]
    notifier = FakeNotifier()

    sent = send_alerts(pending_alerts(events(*rows), NOW), [notifier], NO_SENT, NOW)

    assert len(notifier.texts) == 10
    assert notifier.texts[-1].startswith("...and 16 more events")
    assert len(sent) == 25  # the summarised ones count as sent too
