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
