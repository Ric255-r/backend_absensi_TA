# Aerich Migration Guide

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Generate initial migration

```bash
aerich init -t app.core.database.get_tortoise_config
# If already initialized, skip this.
aerich init-db
```

## 3) Create new migration after model changes

```bash
aerich migrate --name "update_schema"
aerich upgrade
```

## 4) Rollback one version

```bash
aerich downgrade
```

Legacy endpoints are still available under `/api/legacy/*` during transition.

## 2x) Note if data already exists : 
Ini error karena tabel metadata Aerich belum ada: db_absensi_mod.aerich.
aerich upgrade butuh tabel itu untuk mencatat migration yang sudah jalan.
Paling aman untuk kondisi kamu (schema sudah ada):
Buat tabel aerich manual di DB db_absensi_mod:

```bash
CREATE TABLE IF NOT EXISTS `aerich` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `version` VARCHAR(255) NOT NULL,
  `app` VARCHAR(100) NOT NULL,
  `content` JSON NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
Tandai migration sebagai sudah dijalankan (tanpa eksekusi ulang SQL schema):
```bash
python -m aerich upgrade --fake
```
Kenapa --fake? Karena tabel-tabel kamu sudah ada dari dump SQL, jadi cukup register ke history Aerich.
Kalau mau benar-benar eksekusi SQL migration (mis. DB masih kosong), pakai:
```bash
python -m aerich upgrade
```