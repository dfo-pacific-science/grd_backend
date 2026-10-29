# grd backend

Django 5 + Django REST Framework API for the grd Next.js frontend, backed by PostgreSQL.
JWT auth via `djangorestframework-simplejwt`.

## Stack

| Concern        | Choice                                  |
| -------------- | --------------------------------------- |
| Framework      | Django 5.2, DRF 3.18                    |
| Auth           | SimpleJWT (access/refresh tokens)      |
| DB             | PostgreSQL (psycopg 3)                  |
| Filtering      | django-filter, DRF search/ordering      |
| API docs       | drf-spectacular (`/api/docs/`)          |
| CORS           | django-cors-headers                     |
| Config         | env vars via python-dotenv (`.env`)     |

## Setup

```bash
# 1. Activate the virtualenv
.venv\Scripts\activate            # PowerShell: .venv\Scripts\Activate.ps1

# 2. Install deps
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env            # then edit .env with your Postgres details

# 4. Apply migrations + create an admin user
python manage.py migrate
python manage.py createsuperuser   # prompts for email + password

# 5. Run
python manage.py runserver
```

## Layout

```
config/            project settings, root urlconf, wsgi/asgi
accounts/          custom User model (email login) + auth endpoints
grd/               models + API for the `grd` schema  (managed = False)
grd_ref/           models + API for the `grd_ref` schema  (lookup tables)
grd_validation/    models + API for the `grd_validation` schema
manage.py
```

The three schema apps map onto **existing** Postgres tables — every model is
`managed = False`, so Django reads and writes rows but never runs DDL against
them. Table names resolve through `POSTGRES_SEARCH_PATH` (see `.env.example`).
The `grd.*_run_data_v` endpoints are database views and are read-only.

## Auth endpoints

| Method     | Path                       | Purpose                        |
| ---------- | -------------------------- | ------------------------------ |
| GET        | `/api/health/`            | liveness check                 |
| POST       | `/api/auth/register/`     | create account                 |
| POST       | `/api/auth/token/`        | obtain access + refresh (email + password) |
| POST       | `/api/auth/token/refresh/`| rotate access token            |
| POST       | `/api/auth/token/verify/` | validate a token               |
| GET/PATCH  | `/api/auth/me/`           | current user                   |
| GET        | `/api/schema/`            | OpenAPI schema                  |
| GET        | `/api/docs/`              | Swagger UI (browse every endpoint) |

## Data endpoints (full CRUD unless noted)

All under `/api/`, all require `Authorization: Bearer <token>`. Each supports
`?search=`, `?ordering=`, field filters, and page/`page_size` pagination.

**`grd/`** — `workbooks/`, `individuals/` (detail nests results + pbt),
`collection-results/`, `repunit-results/`, `region-results/`, `custom-results/`,
`estimates/`, `inventories/`, `collections-and-groups/`, `baseline-collections/`,
`pbt/`, `extractions/`, `positive-species/`, `negative-species/`, `duplicates/`,
`individual-inventories/`, `run-data/individuals/` *(read-only view)*,
`run-data/inventories/` *(read-only view)*

**`grd-ref/`** — `adipose/`, `estimates-type/`, `gear/`, `id-type/`, `sex/`,
`species/`

**`grd-validation/`** — `file-versions/`, `sheets/`, `mapped-terms/`, `raw-terms/`

Notes: `workbooks/` `sha256` / `file_versions.sha256_checksum` are read-only hex
(create those rows via the pipeline; update works). Deletes are refused by the
DB while FK children exist. PATCH on a JSON column (`attributes`) replaces the
whole object — send the merged value.

## Next.js usage

```ts
// POST /api/auth/token/  ->  { access, refresh }
const res = await fetch(`${API}/api/auth/token/`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password }),
});

// authenticated request
fetch(`${API}/api/auth/me/`, {
  headers: { Authorization: `Bearer ${access}` },
});
```

Set `CORS_ALLOWED_ORIGINS` in `.env` to your frontend origin(s).

## Production / deployment

Full walkthrough for the LXD container in [deploy/README.md](deploy/README.md).
In short:

- Set `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
  and `DJANGO_CSRF_TRUSTED_ORIGINS` / `CORS_ALLOWED_ORIGINS`.
- `gunicorn -c gunicorn.conf.py config.wsgi:application` under systemd
  ([deploy/grd-backend.service](deploy/grd-backend.service)), nginx in front
  ([deploy/nginx.conf](deploy/nginx.conf)).
- `python manage.py collectstatic` — WhiteNoise then serves the admin's static
  files from gunicorn (no nginx filesystem access needed).
