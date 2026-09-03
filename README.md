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

**`grd/`** — `projects/`, `individuals/` (detail nests results + pbt),
`collection-results/`, `repunit-results/`, `region-results/`, `custom-results/`,
`estimates/`, `inventories/`, `collections-and-groups/`, `baseline-files/`,
`pbt/`, `extractions/`, `positive-species/`, `negative-species/`, `duplicates/`,
`individual-inventories/`, `run-data/individuals/` *(read-only view)*,
`run-data/inventories/` *(read-only view)*

**`grd-ref/`** — `adipose/`, `estimates-type/`, `gear/`, `id-type/`, `sex/`,
`species/`

**`grd-validation/`** — `file-versions/`, `sheets/`, `mapped-terms/`, `raw-terms/`

Notes: `projects.sha256` / `file_versions.sha256_checksum` are read-only hex
(create those rows via the pipeline; update works). Deletes are refused by the
DB while FK children exist. PATCH on a JSON column (`attributes`) replaces the
whole object — send the merged value.

## Report endpoints (`reports/` app)

Ports of the old Next.js `app/api/*` routes — raw-SQL joins / pivots / JSONB
aggregation that don't fit a single model. Same query params and the same
`{ data, page, pageSize, total, totalPages }` envelope as the originals, so the
frontend swap is just the base URL. Currently **`AllowAny`** (matches the old
public API); set `PERMISSION` in `reports/views.py` to lock them down.

| Path (`/api/reports/…`) | one row per | extra params |
| --- | --- | --- |
| `individuals` | individual | `species dateFrom dateTo idSource` |
| `bsciDNAResults` | individual | `species dateFrom dateTo idSource` |
| `scBDWRDNA` | individual (top-5 repunits pivoted) | `species dateFrom dateTo idSource` |
| `estimateCatchByStockAge` | individual × repunit | + `probabilityMin probabilityMax` |
| `projects` | project | — (sort only) |
| `sampleCollections` | inventory | `year sampleCode` |
| `stockProportionEstimates` | inventory (repunit stats pivoted) | `year sampleCode` |

Shared params: `page` (`all` or `1,2,…`, 50/page), `sort`, `dir`, `filter`
(full-row text search). Add `/download` to any path for the bare row array with
JSONB columns flattened (for Excel export).

Filter-option lookups: `options/species`, `options/idSources`, `options/years`,
`options/sampleCodes`.

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

## Production notes

- Set `DJANGO_DEBUG=False`, a real `DJANGO_SECRET_KEY`, and `DJANGO_ALLOWED_HOSTS`.
- Serve with `gunicorn config.wsgi` behind a reverse proxy.
- Run `python manage.py collectstatic` for the admin's static files.
