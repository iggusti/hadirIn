"""Pengingat presensi dengan eskalasi per jam untuk Ilham dan Nia.

Dijalankan oleh GitHub Actions pada jam 16.30-21.00 WIB, Senin-Jumat.
State (siapa yang sudah balas, offset Telegram, waktu kirim terakhir)
disimpan di file state.json pada repository yang sama.
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
GH_TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ["REPO"]

# Urutan penting: Ilham lebih dulu, lalu Nia.
PEOPLE = {ILHAM_ID: "Ilham", NIA_ID: "Nia"}
STATE_FILE = "state.json"
START_HOUR, START_MINUTE = 16, 30
MIN_INTERVAL_MINUTES = 50  # jaga-jaga kalau workflow dijalankan manual dua kali


def telegram(method, params=None):
    """Panggil Bot API dengan retry singkat saat kena flood control."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    for attempt in range(4):
        req = urllib.request.Request(url, data=data)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
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
            raise RuntimeError(f"Telegram {method} gagal: {exc.code} {body[:200]}") from exc


def github(method, path, payload=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and method == "GET":
            return None
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"GitHub {method} {path} gagal: {exc.code} {body[:200]}") from exc


def read_state():
    file_info = github("GET", f"contents/{STATE_FILE}")
    if not file_info:
        return {"date": "", "offset": 0, "replied": [], "last_sent": 0}, None
    state = json.loads(base64.b64decode(file_info["content"]).decode())
    return state, file_info["sha"]


def write_state(state, sha):
    payload = {
        "message": "Update state pengingat presensi",
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
        }

    updates = telegram("getUpdates", {"offset": state.get("offset", 0)}).get("result", [])
    if updates:
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

    pending = [name for name in PEOPLE.values() if name not in state["replied"]]
    last_sent = state.get("last_sent", 0)
    interval_ok = now.timestamp() - last_sent >= MIN_INTERVAL_MINUTES * 60

    if pending and (first_run or interval_ok):
        who = ", ".join(pending)
        if first_run:
            text = (
                "⏰ Pengingat presensi 16.30 WIB\n\n"
                f"Sudah presensi hari ini, {who}?\n"
                "Balas pesan ini di grup ya ✅"
            )
        else:
            text = (
                "⏰ Pengingat presensi\n\n"
                f"Belum balas: {who}.\n"
                "Sudah presensi? Balas di grup ya ✅"
            )
        telegram("sendMessage", {"chat_id": CHAT_ID, "text": text})
        state["last_sent"] = now.timestamp()

    write_state(state, sha)
    print(
        f"{now:%Y-%m-%d %H:%M WIB} | sudah balas: {state['replied'] or '-'} | "
        f"belum balas: {pending or '-'} | dikirim: {bool(pending and (first_run or interval_ok))}"
    )


if __name__ == "__main__":
    main()
