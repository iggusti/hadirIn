# AGENTS.md

Instructions for agents working on this repository.

## Project

`hadirIn` is a Telegram attendance reminder bot for Ilham and Nia. It sends a
reminder at 16:30 WIB on weekdays, then escalates hourly until 21:00 WIB only
to people who have not replied in the group. Once both have replied, it sends
one thank-you message and stops for the day.

## Active files

- `attendance_bot.py` — the active bot. Uses only the Python standard library.
- `simple_reminder_bot.py` — legacy one-shot version; do not use for new work.
- `.github/workflows/reminder.yml` — GitHub Actions workflow.
- `state.json` — runtime state, created/updated by the bot. Never edit by hand
  unless debugging, and never commit secrets inside it.

## Rules

1. Keep all code, comments, filenames, messages, and documentation in English.
2. Never put tokens, chat IDs, or Telegram user IDs in README or any tracked
   file. Secrets belong only in `.env` (local, gitignored) and GitHub Secrets.
3. Never commit `.env`.
4. GitHub Actions evaluates `cron` in UTC. The `timezone` option was tested and
   was not honoured on this repository. Use explicit UTC values:
   - `30 9,10,11,12,13 * * 1-5` = 16:30-20:30 WIB
   - `0 14 * * 1-5` = 21:00 WIB
5. GitHub `schedule` events are not reliable here. The recommended trigger is
   cron-job.org calling the `workflow_dispatch` endpoint hourly.
6. The bot's own window guard prevents sends outside 16:30-21:00 WIB unless
   `FORCE=true`. `DRY_RUN=true` exercises logic without sending or writing
   state, and reads Telegram updates without an offset so no reply is
   acknowledged. Use it for safe tests.
7. Deduplication is intentional: at most one send per 50 minutes, and one
   thank-you per day via the `thanked` flag. Do not remove these guards.

## Environment notes for this workspace

- Plain `git push` and `curl` crash here because of a broken libcurl. Use
  `gh api` for GitHub operations, or `dulwich` if a real git push is needed.
- Updating files under `.github/workflows/` via the GitHub API requires the
  `workflow` scope. Refresh it with `gh auth refresh -s workflow --hostname github.com`.
- Verify workflow changes with `gh api repos/iggusti/hadirIn/actions/workflows`
  and inspect runs with `gh run view <id> --log`.

## Safe test command

Run a dry check locally with environment variables from `.env`, plus
`ILHAM_ID`, `NIA_ID`, `NIA_ID_2`, `GH_TOKEN`, `REPO`, and `DRY_RUN=true`.
