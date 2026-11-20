"""Small webhook receiver that verifies signatures.

It stands in for whatever system would consume the alerts, and is not deployed.
It does not import the collector: a real receiver is written by someone else and only
shares the secret. Run locally (WEBHOOK_SECRET must match the collector's):

    uvicorn demo.receiver:app --port 8001
"""
import hashlib
import hmac
import json
import logging
import os
import time

from fastapi import FastAPI, HTTPException, Request

log = logging.getLogger("receiver")

MAX_AGE_SECONDS = 5 * 60
TIMESTAMP_HEADER = "X-Monitor-Timestamp"
SIGNATURE_HEADER = "X-Monitor-Signature"


def verify(secret, timestamp, signature, body, now):
    """None if the message is genuine and fresh, otherwise the reason it is not."""
    if not secret:
        # Fail closed: a receiver started without its secret accepts nothing.
        return "receiver has no secret configured"
    if timestamp is None or signature is None:
        return "missing signature headers"
    if not timestamp.isdigit():
        return "timestamp is not a number"
    # Both directions: an old message may be a replay; one from the future means a broken clock.
    if abs(now - int(timestamp)) > MAX_AGE_SECONDS:
        return "timestamp outside the 5-minute window"

    expected = "sha256=" + hmac.new(
        secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256
    ).hexdigest()
    # compare_digest always looks at every character. A plain == stops at the first
    # difference, and that tiny time difference can leak the signature bit by bit.
    if not hmac.compare_digest(expected.encode(), signature.encode()):
        return "signature does not match"
    return None


def create_app(secret, clock=time.time):
    app = FastAPI(title="Alert receiver (demo)")
    # alert_ids already handled. A retry from the collector or a replay inside the 5-minute
    # window is answered without acting twice. In memory only: fine for a demo, a real
    # receiver would keep this in its database.
    seen = set()

    @app.post("/events")
    async def receive(request: Request):
        # The raw bytes, not parsed JSON: the signature is over exactly what was sent.
        body = await request.body()
        problem = verify(
            secret,
            request.headers.get(TIMESTAMP_HEADER),
            request.headers.get(SIGNATURE_HEADER),
            body,
            clock(),
        )
        if problem:
            # The real reason goes to our log only. Telling the caller "your timestamp is
            # too old" would help an attacker adjust.
            log.warning("rejected: %s", problem)
            raise HTTPException(status_code=401, detail="invalid signature")

        event = json.loads(body)
        if event["alert_id"] in seen:
            return {"status": "duplicate"}
        seen.add(event["alert_id"])
        log.info("accepted %s: %s", event["alert_id"], event["text"])
        return {"status": "accepted"}

    return app


app = create_app(os.environ.get("WEBHOOK_SECRET", ""))
