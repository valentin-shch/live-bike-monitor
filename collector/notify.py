"""Notifiers. All off unless their env vars are set."""
import json
import logging
import os
from zoneinfo import ZoneInfo

import pandas as pd

from collector.config import ALERT_MAX_AGE, ALERT_STATES, DISPLAY_TZ, MAX_ALERTS_PER_RUN
from collector.http import HttpError

log = logging.getLogger(__name__)
SENT_COLUMNS = ["alert_id", "channel", "sent_at"]
JSON = {"Content-Type": "application/json"}


# ---------- the interface: anything with a name and send(text) ----------

class TelegramNotifier:
    name = "telegram"

    def __init__(self, client, token, chat_id):
        self.client, self.token, self.chat_id = client, token, chat_id

    def send(self, text):
        body = json.dumps({"chat_id": self.chat_id, "text": text}).encode()
        # The token is part of the URL path, so the label is what reaches the logs.
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.client.post(url, body, JSON, label="telegram sendMessage")


class SlackNotifier:
    name = "slack"

    def __init__(self, client, webhook_url):
        self.client, self.webhook_url = client, webhook_url

    def send(self, text):
        body = json.dumps({"text": text}).encode()
        # For Slack the whole URL is the secret: anyone who has it can post to the channel.
        self.client.post(self.webhook_url, body, JSON, label="slack webhook")


def configured_notifiers(client, env=None):
    """Only the channels whose variables are set. An empty value counts as not set,
    so a blank line copied from .env.example keeps the channel off."""
    env = os.environ if env is None else env
    notifiers = []
    if env.get("TELEGRAM_BOT_TOKEN") and env.get("TELEGRAM_CHAT_ID"):
        notifiers.append(TelegramNotifier(client, env["TELEGRAM_BOT_TOKEN"], env["TELEGRAM_CHAT_ID"]))
    if env.get("SLACK_WEBHOOK_URL"):
        notifiers.append(SlackNotifier(client, env["SLACK_WEBHOOK_URL"]))
    return notifiers


# ---------- from events to alerts ----------

def pending_alerts(events, now, max_age=ALERT_MAX_AGE):
    """Every start and every end of an alert-worthy episode that happened recently.

    Each alert gets a stable alert_id, so "was this one already sent?" has a yes/no answer.
    """
    worthy = events[events["state"].isin(ALERT_STATES)].copy()
    for col in ("started_at", "ended_at"):
        worthy[col] = pd.to_datetime(worthy[col], utc=True)

    started = worthy.assign(kind="started", at=worthy["started_at"])
    finished = worthy[worthy["ended_at"].notna()]
    ended = finished.assign(kind="ended", at=finished["ended_at"])
    alerts = pd.concat([started, ended], ignore_index=True)
    alerts = alerts[alerts["at"] >= now - max_age]

    alerts["alert_id"] = (
        alerts["scope"] + ":" + alerts["subject"].astype(str) + ":" + alerts["state"] + ":"
        + alerts["started_at"].dt.strftime("%Y-%m-%dT%H:%MZ") + ":" + alerts["kind"]
    )
    return alerts.sort_values("at", ignore_index=True)


def message(alert, tz=ZoneInfo(DISPLAY_TZ)):
    since = alert.started_at.astimezone(tz).strftime("%H:%M")
    at = alert.at.astimezone(tz).strftime("%H:%M")
    texts = {
        ("offline", "started"): f"Station {alert.subject} offline since {since}",
        ("offline", "ended"): f"Station {alert.subject} back online at {at} (offline since {since})",
        ("stale", "started"): f"Feed stale since {since}: no new data from Bicing",
        ("stale", "ended"): f"Feed updating again at {at} (stale since {since})",
        ("missing", "started"): f"Stations missing from the feed since {since}",
        ("missing", "ended"): f"Missing stations back in the feed at {at} (since {since})",
    }
    return texts[(alert.state, alert.kind)]


def send_alerts(alerts, notifiers, sent, now, limit=MAX_ALERTS_PER_RUN):
    """Send each alert once per channel. Returns the rows to add to alerts_sent.

    Order: send first, record after. A crash between the two means the next run sends it
    again (at least once). The other order could lose an alert forever (at most once).
    """
    new_rows = []
    for notifier in notifiers:
        done = set(sent.loc[sent["channel"] == notifier.name, "alert_id"])
        todo = alerts[~alerts["alert_id"].isin(done)]
        for text, ids in _batches(todo, limit):
            try:
                notifier.send(text)
            except HttpError as exc:
                # This channel is probably down: stop here, the next run tries the rest.
                log.warning("%s: %s", notifier.name, exc)
                break
            new_rows += [(alert_id, notifier.name, now) for alert_id in ids]
    return pd.DataFrame(new_rows, columns=SENT_COLUMNS)


def _batches(todo, limit):
    rows = list(todo.itertuples(index=False))
    if len(rows) <= limit:
        return [(message(a), [a.alert_id]) for a in rows]
    head, rest = rows[: limit - 1], rows[limit - 1 :]
    summary = f"...and {len(rest)} more events. See the status page for the full list."
    return [(message(a), [a.alert_id]) for a in head] + [(summary, [a.alert_id for a in rest])]
