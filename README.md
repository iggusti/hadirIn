# hadirIn — Telegram Attendance Reminder

A Telegram bot that reminds **Ilham** and **Nia** to check in for attendance on weekdays.

## How it works

- At **16:30 WIB**, the bot sends a reminder to the group with Ilham, Nia, and the bot.
- Every hour after that (17:30, 18:30, 19:30, 20:30, and finally **21:00 WIB**), the bot checks who has replied in the group.
- Anyone who has already replied is no longer reminded. Anyone who has not replied keeps getting reminders.
- Once both have replied, the bot stops until the next weekday.
- Runs **Monday to Friday** only. State resets automatically at 16:30 WIB each day.

Example follow-up message when Nia has not replied:

```
⏰ Attendance reminder

Still no reply from: Nia.
Have you checked in? Reply in the group ✅
```

## Files

| File | Purpose |
| --- | --- |
| `attendance_bot.py` | Main logic: read updates, match user IDs, send reminders, save state. |
| `state.json` | Created automatically in the repo. Stores the date, Telegram offset, who replied, and the last send time. Contains no tokens. |
| `.github/workflows/reminder.yml` | GitHub Actions schedule. |
| `simple_reminder_bot.py` | Legacy one-shot version (single 16:30 reminder, no escalation). |

## Schedule

GitHub Actions uses UTC:

```
30 9,10,11,12,13 * * 1-5   -> 16:30-20:30 WIB
0 14 * * 1-5               -> 21:00 WIB (final reminder)
```

## GitHub Secrets

| Secret | Value |
| --- | --- |
| `BOT_TOKEN` | Bot token from @BotFather |
| `CHAT_ID` | Telegram group ID where reminders are sent |
| `ILHAM_ID` | Ilham's Telegram user ID |
| `NIA_ID` | Nia's first Telegram user ID |
| `NIA_ID_2` | Nia's second Telegram user ID |

Nia has two accounts; a reply from either one counts as a reply from Nia.

The workflow uses the built-in `GITHUB_TOKEN` with `contents: write` permission to save `state.json`.

## Manual run

Open the **Actions** tab, select **Attendance Reminder**, then click **Run workflow**.

Two optional inputs are available:

- `force`: send even outside 16:30-21:00 WIB.
- `dry_run`: exercise the logic without sending messages or changing state.

Manual runs outside the reminder window are skipped by default, so they cannot send a message at the wrong time. Sends are also limited to at most once every 50 minutes to avoid duplicates.

## Notes

- GitHub Actions may delay scheduled runs by a few minutes during peak load.
- Scheduled workflows can be disabled automatically after about 60 days of repository inactivity.
- Do not commit `.env`. The bot token should only live in GitHub Secrets.
