# hadirIn — Telegram Attendance Reminder

A Telegram bot that reminds **Ilham** and **Nia** to check in for attendance on weekdays.

## How it works

- At **16:30 WIB**, the bot sends a reminder to the group with Ilham, Nia, and the bot.
- After that it checks every **30 minutes** — 17:00, 17:30, 18:00, 18:30, 19:00, 19:30, 20:00, 20:30, and finally **21:00 WIB**.
- At every check, a reminder is sent if anyone is still pending. Someone who replied is no longer named in the reminder; someone who has not replied keeps getting reminded at every slot.
- Once both have replied, the next check sends a short thank-you message and the bot stops until the next weekday. The thank-you is sent only once per day.
- Runs **Monday to Friday** only. State resets automatically at 16:30 WIB each day.

Example follow-up message when Nia has not replied:

```
⏰ Attendance reminder

Still no reply from: Nia.
Have you checked in? Reply in the group ✅
```

Message sent once both have replied:

```
✅ Both check-ins confirmed.
Thank you, Ilham and Nia — have a productive day.
```

## Files

| File | Purpose |
| --- | --- |
| `attendance_bot.py` | Main logic: read updates, match user IDs, send reminders, save state. |
| `state.json` | Created automatically in the repo. Stores the date, Telegram offset, who replied, the last send slot, and whether the thank-you was sent. Contains no tokens. |
| `.github/workflows/reminder.yml` | GitHub Actions schedule. |
| `simple_reminder_bot.py` | Legacy one-shot version (single 16:30 reminder, no escalation). |
| `AGENTS.md` | Instructions for coding agents working on this repository. |

## Schedule

GitHub Actions evaluates `cron` in UTC, so the schedule is written in UTC:

```
30 9 * * 1-5          -> 16:30 WIB (first reminder)
0,30 10-13 * * 1-5   -> 17:00, 17:30, 18:00, 18:30, 19:00, 19:30, 20:00, 20:30 WIB
0 14 * * 1-5          -> 21:00 WIB (final reminder)
```

The `timezone` option was tested but was not honoured on this repository, so explicit UTC is used instead. GitHub Actions schedules are best-effort and can be delayed or dropped during peak load.

## Reliable trigger (recommended)

Because the built-in `schedule` event is unreliable here, use free
[cron-job.org](https://cron-job.org/) jobs to call the `workflow_dispatch`
endpoint every 30 minutes. A successful call returns `204 No Content`.

| Setting | Value |
| --- | --- |
| URL | `https://api.github.com/repos/iggusti/hadirIn/actions/workflows/428908062/dispatches` |
| Method | `POST` |
| Header | `Authorization: Bearer <PAT>` |
| Header | `Accept: application/vnd.github+json` |
| Header | `X-GitHub-Api-Version: 2022-11-28` |
| Header | `Content-Type: application/json` |
| Header | `User-Agent: hadirIn-cron` |
| Body | `{"ref":"main","inputs":{"force":false,"dry_run":false}}` |
| Timezone | `Asia/Jakarta` |

Create three jobs with these crontab expressions:

```
30 16 * * 1-5         -> 16:30 WIB
0,30 17-20 * * 1-5   -> 17:00-20:30 WIB, every 30 minutes
0 21 * * 1-5         -> 21:00 WIB
```

The PAT must be a fine-grained token scoped to this repository with
**Actions: read and write**. A `403` usually means a missing `User-Agent`
header, a wrong token, or insufficient permission. Never paste the PAT into
this README or any tracked file.

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

- `force`: send even outside 16:30-21:00 WIB or within the same 30-minute slot.
- `dry_run`: exercise the logic without sending messages or changing state.

Manual runs outside the reminder window are skipped by default. Reminders are limited to at most one per 30-minute slot, so duplicate triggers in the same slot do not send twice. A new slot always sends again if somebody is still pending.

## Notes

- GitHub Actions may delay scheduled runs by a few minutes during peak load.
- Scheduled workflows can be disabled automatically after about 60 days of repository inactivity.
- Do not commit `.env`. The bot token should only live in GitHub Secrets.

## License

Released under the [MIT License](LICENSE).
