# hadirIn — Pengingat presensi Telegram

Bot Telegram yang mengingatkan **Ilham** dan **Nia** untuk presensi setiap hari kerja.

## Cara kerja

- Mulai **16.30 WIB**, bot kirim pengingat ke grup berisi Ilham + Nia + bot.
- Setiap **1 jam** setelahnya (17.30, 18.30, 19.30, 20.30, dan terakhir **21.00 WIB**), bot cek siapa yang sudah membalas di grup.
- Yang **sudah balas** tidak diingatkan lagi. Yang **belum balas** tetap dapat pengingat.
- Kalau dua-duanya sudah balas, bot **berhenti** sampai hari kerja berikutnya.
- Berlaku **Senin–Jumat** saja. State reset otomatis tiap hari jam 16.30 WIB.

Contoh pesan lanjutan kalau Nia belum balas:

```
⏰ Pengingat presensi

Belum balas: Nia.
Sudah presensi? Balas di grup ya ✅
```

## Arsitektur

- `presensi_bot.py` — logika utama: baca `getUpdates`, cocokkan user ID, kirim pengingat, simpan state.
- `state.json` — disimpan otomatis di repo berisi tanggal, `offset` Telegram, daftar yang sudah balas, dan waktu kirim terakhir. File ini tidak berisi token.
- `.github/workflows/reminder.yml` — penjadwal GitHub Actions.

Jadwal cron (GitHub Actions memakai UTC):

```
30 9,10,11,12,13 * * 1-5   -> 16.30-20.30 WIB
0 14 * * 1-5               -> 21.00 WIB (batas terakhir)
```

## GitHub Secrets yang dipakai

| Secret | Isi |
| --- | --- |
| `BOT_TOKEN` | Token bot dari @BotFather |
| `CHAT_ID` | ID grup Telegram (`-5386255651`) |
| `ILHAM_ID` | Telegram user ID Ilham (`959004639`) |
| `NIA_ID` | Telegram user ID Nia (`949805387`) |

Workflow memakai `GITHUB_TOKEN` bawaan dengan izin `contents: write` untuk menyimpan `state.json`.

## Uji coba

Buka tab **Actions** → pilih **Pengingat Presensi** → **Run workflow**.

Catatan: run manual di luar jam 16.30–21.00 tetap aman — script hanya menganggap "hari ini" dimulai pukul 16.30 WIB, dan pengiriman dibatasi minimal 50 menit sekali supaya tidak spam.

## Catatan

- GitHub Actions bisa menunda scheduled run beberapa menit saat sedang sibuk.
- Scheduled workflow bisa nonaktif otomatis setelah ~60 hari tanpa aktivitas di repo.
- `reminder_bot.py` adalah versi lama (pengingat sekali jam 16.30, tanpa eskalasi). Versi yang aktif sekarang adalah `presensi_bot.py`.
- Jangan commit file `.env`. Token bot harus tetap hanya ada di GitHub Secrets.
