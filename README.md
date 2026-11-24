# hadirIn — Pengingat presensi Telegram (16.30 WIB)

Bot mengirim satu pesan pengingat setiap **Senin–Jumat pukul 16.30 WIB** ke chat yang dipakai berdua (Anda + istri). Isi pesan menyebut tempat kerja masing-masing: MAN 2 Cilegon dan Universitas Telkom.

Pilih **salah satu** cara di bawah.

---

## Persiapan yang sama untuk kedua cara

### 1. Pastikan bot sudah ada
Jika belum, buka Telegram, cari **@BotFather**, kirim `/newbot`, ikuti instruksi, dan simpan **token** yang diberikan. Bot Anda yang sekarang sudah punya token — pakai token itu.

### 2. Dapatkan CHAT_ID
Tambahkan bot ke chat yang dipakai berdua. Bisa grup berisi Anda, istri, dan bot, atau chat private jika memang hanya itu yang dipakai.

Cara paling mudah:

1. Di chat tersebut, kirim pesan apa saja (misalnya `halo`).
2. Buka di browser: `https://api.telegram.org/bot<TOKEN_ANDA>/getUpdates`
3. Cari bagian `"chat": {"id": ...}`. Angka itulah `CHAT_ID`.
   - Chat private: angka positif, misal `123456789`
   - Grup: angka negatif biasanya diawali `-100`, misal `-1001234567890`

> Chat ID itu unik untuk setiap chat. Kalau bot dipindah ke grup lain, ID-nya berubah.

---

## Cara A — Bot Python (butuh perangkat yang menyala terus)

Cocok kalau punya VPS, Raspberry Pi, atau komputer yang tidak dimatikan. Mudah dikembangkan kalau nanti mau ada tombol check-in.

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env, isi BOT_TOKEN dan CHAT_ID

# Supaya env variable terbaca:
set -a && source .env && set +a   # Windows: pakai python-dotenv atau set manual
python reminder_bot.py
```

Uji dengan mengirim `/test` ke bot — pengingat contoh akan langsung muncul. `/start` menampilkan chat ID dari chat tempat perintah dikirim.

Supaya tetap jalan setelah terminal ditutup, misalnya dengan systemd. Contoh `/etc/systemd/system/presensi.service`:

```ini
[Unit]
Description=Pengingat presensi Telegram
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/path/ke/folder/ini
EnvironmentFile=/path/ke/folder/ini/.env
ExecStart=/path/ke/folder/ini/venv/bin/python /path/ke/folder/ini/reminder_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Lalu:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now presensi
sudo systemctl status presensi
```

---

## Cara B — GitHub Actions (tanpa server, gratis)

Cocok kalau tidak mau menyalakan komputer/VPS 24 jam. Jadwal dijalankan oleh GitHub.

1. Buat repository GitHub (boleh private), upload file `.github/workflows/reminder.yml` dari folder ini.
2. Di repository: **Settings → Secrets and variables → Actions → New repository secret**
   - Nama `BOT_TOKEN`, isi token bot
   - Nama `CHAT_ID`, isi chat ID dari langkah persiapan
3. Buka tab **Actions**, pilih workflow **Pengingat Presensi**, klik **Run workflow** untuk uji coba. Kalau pesan masuk, jadwal otomatisnya aktif.

Catatan: GitHub bisa menunda eksekusi beberapa menit saat server sedang sibuk, dan scheduled workflow bisa mati otomatis setelah ~60 hari repo tidak ada aktivitas. Untuk pengingat presensi, keterlambatan beberapa menit biasanya masih acceptable, tapi kalau harus tepat 16.30, pakai Cara A.

---

## Menyesuaikan pesan atau jadwal

- **Isi pesan:** ubah variabel `PESAN` di `reminder_bot.py` (Cara A) atau blok `PESAN` di `reminder.yml` (Cara B).
- **Jam:** Cara A ubah `hour=16, minute=30`. Cara B ubah cron `30 9 * * 1-5` — ingat cron GitHub pakai UTC, jadi 09.30 UTC = 16.30 WIB.
- **Hari:** `days=(0,1,2,3,4)` / `1-5` berarti Senin–Jumat. Kalau mau setiap hari, pakai `days=(0,1,2,3,4,5,6)` / `1-7` (atau `*`).
- **Libur nasional:** kedua cara belum mengenali tanggal merah. Kalau mau skip libur, beri tahu saya, nanti saya tambahkan daftar libur atau pengecekan kalender.
