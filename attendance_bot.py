"""Attendance reminder bot with hourly escalation for Ilham and Nia.

Runs through GitHub Actions between 16:30 and 21:00 WIB, Monday to Friday.
State (who replied, Telegram update offset, last send time) is stored in
state.json in the same repository.
"""

import base64
import datetime as dt
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

WIB = ZoneInfo("Asia/Jakarta")
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])
ILHAM_ID = int(os.environ["ILHAM_ID"])
NIA_ID = int(os.environ["NIA_ID"])
NIA_ID_2 = int(os.environ.get("NIA_ID_2", "0") or 0)
GH_TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ["REPO"]

STATE_FILE = "state.json"
START_HOUR, START_MINUTE = 16, 30
END_HOUR, END_MINUTE = 21, 0
MIN_INTERVAL_MINUTES = 50  # guard against duplicate manual runs


def env_flag(name):
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


DRY_RUN = env_flag("DRY_RUN")
FORCE = env_flag("FORCE")

# Order matters: Ilham first, then Nia.
# Nia has two accounts; a reply from either one counts as a reply from Nia.
PEOPLE = {ILHAM_ID: "Ilham", NIA_ID: "Nia"}
if NIA_ID_2:
    PEOPLE[NIA_ID_2] = "Nia"


def telegram(method, params=None):
    """Call the Bot API, retrying briefly when rate limited."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    for attempt in range(4):
        request = urllib.request.Request(url, data=data)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            if exc.code == 429 and attempt < 3:
                try:
                    delay = json.loads(body).get("parameters", {}).get("retry_after", 5)
                except ValueError:
                    delay = 5
                time.sleep(min(int(delay) + 1, 30))
                continue
            raise RuntimeError(f"Telegram {method} failed: {exc.code} {body[:200]}") from exc


def github(method, path, payload=None):
    """Read or write a file through the GitHub contents API."""
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and method == "GET":
            return None
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub {method} {path} failed: {exc.code} {body[:200]}") from exc


def read_state():
    file_info = github("GET", f"contents/{STATE_FILE}")
    if not file_info:
        return {"date": "", "offset": 0, "replied": [], "last_sent": 0, "thanked": False}, None
    state = json.loads(base64.b64decode(file_info["content"]).decode())
    return state, file_info["sha"]


def write_state(state, sha):
    payload = {
        "message": "Update attendance reminder state",
        "content": base64.b64encode(json.dumps(state).encode()).decode(),
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha
    github("PUT", f"contents/{STATE_FILE}", payload)


def main():
    now = dt.datetime.now(WIB)
    today = now.date().isoformat()
    day_start = dt.datetime.combine(
        now.date(), dt.time(START_HOUR, START_MINUTE), tzinfo=WIB
    ).timestamp()

    state, sha = read_state()
    first_run = state.get("date") != today
    if first_run:
        state = {
            "date": today,
            "offset": state.get("offset", 0),
            "replied": [],
            "last_sent": 0,
            "thanked": False,
        }

    # In dry-run mode, read updates without an offset so Telegram does not
    # acknowledge them. Otherwise a later real run would never see those replies.
    params = {} if DRY_RUN else {"offset": state.get("offset", 0)}
    updates = telegram("getUpdates", params).get("result", [])
    if updates and not DRY_RUN:
        state["offset"] = max(item["update_id"] for item in updates) + 1

    for item in updates:
        message = item.get("message") or item.get("edited_message") or {}
        if not message:
            continue
        sender = message.get("from", {})
        if sender.get("is_bot"):
            continue
        if message.get("chat", {}).get("id") != CHAT_ID:
            continue
        if message.get("date", 0) < day_start:
            continue
        name = PEOPLE.get(sender.get("id"))
        if name and name not in state["replied"]:
            state["replied"].append(name)

    pending = list(
        dict.fromkeys(name for name in PEOPLE.values() if name not in state["replied"])
    )
    last_sent = state.get("last_sent", 0)
    interval_ok = now.timestamp() - last_sent >= MIN_INTERVAL_MINUTES * 60
    in_window = dt.time(START_HOUR, START_MINUTE) <= now.time() <= dt.time(END_HOUR, END_MINUTE)
    allowed = in_window or FORCE

    sent = False
    if pending and (first_run or interval_ok) and allowed:
        who = ", ".join(pending)
        if first_run:
            text = (
                "⏰ Attendance reminder 16:30 WIB\n\n"
                f"Have you checked in today, {who}?\n"
                "Reply in the group ✅"
            )
        else:
            text = (
                "⏰ Attendance reminder\n\n"
                f"Still no reply from: {who}.\n"
                "Have you checked in? Reply in the group ✅"
            )
        if not DRY_RUN:
            telegram("sendMessage", {"chat_id": CHAT_ID, "text": text})
            state["last_sent"] = now.timestamp()
        sent = not DRY_RUN

    just_completed = not pending and not state.get("thanked", False)
    if just_completed and allowed:
        text = (
            "✅ Both check-ins confirmed.\n"
            "Thank you, Ilham and Nia — have a productive day."
        )
        if not DRY_RUN:
            telegram("sendMessage", {"chat_id": CHAT_ID, "text": text})
            state["thanked"] = True
            state["last_sent"] = now.timestamp()
        sent = not DRY_RUN

    if not DRY_RUN:
        write_state(state, sha)
    print(
        f"{now:%Y-%m-%d %H:%M WIB} | replied: {state['replied'] or '-'} | "
        f"pending: {pending or '-'} | thanked: {state.get('thanked', False)} | "
        f"sent: {sent} | dry_run: {DRY_RUN}"
    )


if __name__ == "__main__":
    main()
