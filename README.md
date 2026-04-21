# Backend Absensi

Backend Absensi adalah API FastAPI untuk sistem presensi karyawan berbasis akun,
device binding, foto, jadwal kerja, hari libur, pengajuan ketidakhadiran,
dashboard admin, audit log, websocket realtime, export Excel, dan subscription
gate.

## Fitur Utama

- Login JWT untuk user dan admin.
- Device binding untuk akses mobile.
- Check-in dan check-out dengan foto dan koordinat.
- Validasi jadwal kerja, toleransi terlambat, dan hari libur.
- Pengajuan cuti, sakit, dan izin dengan approval admin.
- Dashboard admin, analytics, dan export laporan Excel.
- Audit log untuk perubahan data penting.
- Websocket untuk update absensi realtime.
- Subscription guard untuk membatasi akses aplikasi saat subscription expired.
- Internal job endpoint untuk expire subscription.

## Tech Stack

- Python 3.11
- FastAPI
- Tortoise ORM
- Aerich migration
- MySQL
- OpenPyXL
- Uvicorn

## Struktur Project

- `app/routers`: definisi endpoint API.
- `app/controllers`: business logic.
- `app/models`: model Tortoise ORM.
- `app/schemas`: request dan response schema.
- `app/core`: config, database, audit, password, serializer, subscription.
- `app/dependencies`: dependency FastAPI untuk auth dan subscription guard.
- `migrations`: migration Aerich.
- `services`: script/service pendukung.
- `storage/uploads`: lokasi default file upload baru.

## Konfigurasi

Salin `.env.example` menjadi `.env`, lalu isi secret sesuai environment.

```env
JWT_SECRET_KEY=change-this-secret
INTERNAL_JOB_TOKEN=change-this-internal-token
ENABLE_LEGACY_ROUTES=false
UPLOAD_STORAGE_DIR=storage/uploads
CORS_ALLOW_ORIGINS=http://localhost:5173,http://localhost:3000
```

Database saat ini masih memakai `koneksi_config.txt` dengan format:

```txt
db_name,host,user,password,port
```

## Menjalankan Aplikasi

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 5500 --reload
```

Dokumentasi Swagger tersedia di:

```txt
http://localhost:5500/docs
```

## Endpoint Portfolio Yang Menonjol

- `POST /api/login`
- `GET /api/user`
- `POST /api/absen/check_in`
- `PUT /api/absen/check_out`
- `GET /api/admin/get_analytics`
- `GET /api/admin/analytics/employee/{id_karyawan}`
- `GET /api/subscription/status`
- `POST /api/admin/subscriptions`
- `PUT /api/admin/subscriptions/{id_subscription}/extend`
- `PUT /api/admin/subscriptions/{id_subscription}/expire`
- `GET /api/admin/subscriptions/{id_subscription}/history`
- `GET /api/admin/audit-logs`
- `GET /api/admin/audit-logs/export`
- `GET /api/admin/export_excel`
- `POST /api/internal/subscriptions/expire`
- `WS /api/admin/ws-absensi`

## Attendance Intelligence

Endpoint `GET /api/admin/analytics/employee/{id_karyawan}` menyediakan profil
performa absensi per karyawan, termasuk:

- punctuality score;
- attendance rate;
- on-time rate;
- tren mingguan dan bulanan;
- pola keterlambatan per hari;
- pola izin/cuti dekat weekend.

Contoh:

```txt
GET /api/admin/analytics/employee/KRY001?start_date=2026-03-01&end_date=2026-03-31
```

## Subscription Management

Subscription status tersedia untuk frontend melalui:

```txt
GET /api/subscription/status
```

Admin dan owner dapat mengelola subscription tanpa diblokir subscription gate:

```txt
GET /api/admin/subscriptions
POST /api/admin/subscriptions
PUT /api/admin/subscriptions/{id_subscription}/extend
PUT /api/admin/subscriptions/{id_subscription}/expire
GET /api/admin/subscriptions/{id_subscription}/history
```

Subscription memiliki grace period 3 hari setelah `end_at`. Selama grace period,
status frontend akan menjadi `grace_period`.

## Audit Log Viewer

Audit log dapat dilihat dan difilter dari endpoint:

```txt
GET /api/admin/audit-logs?actor=admin&action=edit&table_name=karyawan&start_date=2026-04-01&end_date=2026-04-30
```

Export CSV tersedia di:

```txt
GET /api/admin/audit-logs/export
```

## Catatan Legacy

Route legacy tidak aktif secara default. Untuk mengaktifkan sementara:

```env
ENABLE_LEGACY_ROUTES=true
```

Untuk portfolio, gunakan route modern di bawah prefix `/api` dan biarkan legacy
tetap nonaktif.
