# `reports` app

Read-only **reporting endpoints** for the GRD dataset — the multi-table joins,
pivots and JSONB aggregations that power the tabs on the frontend's
`/viewData` and `/apiPage` screens.

These are ports of the old Next.js data layer (`grd-nextjs/app/api/*` +
`grd-nextjs/lib/queries/*`). Each endpoint keeps the **same query parameters**
and the **same response envelope** as the route it replaces, so moving the
frontend onto this backend is a base-URL change, not a rewrite.

---

## Why this is a separate app (and raw SQL)

The CRUD apps (`grd`, `grd_ref`, `grd_validation`) expose one model per table.
Reports are different:

- **`scBDWRDNA`** pivots the top-5 `individuals_repunit_results` rows for each
  individual into `repunit_1..5` / `probability_1..5` columns
  (`ROW_NUMBER() OVER (PARTITION BY …)`).
- **`stockProportionEstimates`** aggregates `grd.estimates` into a single
  `repunit -> {point_estimate, standard_deviation, …}` JSONB map per inventory
  (`jsonb_object_agg`).
- **`filter`** is a full-row text search (`i::text ILIKE %s`).
- Column lists, aliases and CASE expressions are fixed by the report.

The Django ORM models these poorly. Reproducing the original SQL verbatim is
simpler, faster, and guarantees identical results, so each report runs as a
parameterised raw query in [`sql.py`](sql.py).

---

## Files

| File | Purpose |
| --- | --- |
| [`sql.py`](sql.py) | SQL fragments (`SELECT` / `FROM` / `WHERE` builders), the `REPORTS` registry, `run_report()`, and the option lookups. All DB access lives here. |
| [`views.py`](views.py) | Thin function-based views: parse query params → `run_report()` → `Response`. |
| [`urls.py`](urls.py) | URL map, mirroring the old Next.js route paths. |

No models, no migrations — the app never touches the schema.

---

## Endpoints

Base path: **`/api/reports/`**

### Report tables

| Path | One row per | Report-specific params |
| --- | --- | --- |
| `individuals` | individual | `species`, `dateFrom`, `dateTo`, `idSource` |
| `bsciDNAResults` | individual | `species`, `dateFrom`, `dateTo`, `idSource` |
| `scBDWRDNA` | individual (top-5 repunits pivoted in) | `species`, `dateFrom`, `dateTo`, `idSource` |
| `estimateCatchByStockAge` | individual × repunit | `species`, `dateFrom`, `dateTo`, `idSource`, `probabilityMin`, `probabilityMax` |
| `projects` | project | — (sort only) |
| `sampleCollections` | inventory | `year`, `sampleCode` |
| `stockProportionEstimates` | inventory (repunit stats pivoted in) | `year`, `sampleCode` |

### Shared params (every report)

| Param | Type | Default | Notes |
| --- | --- | --- | --- |
| `page` | `all` \| `1,2,…` | `all` | `all` = every matching row unpaginated; an integer = that page of 50. |
| `sort` | string | — | Column name. Validated against `^[A-Za-z_][A-Za-z0-9_]*$` before it goes into `ORDER BY` — anything else is ignored. |
| `dir` | `asc` \| `desc` | `asc` | |
| `filter` | string | — | Free-text `ILIKE` search across the whole row. |

Multi-value params (`species`, `idSource`, `year`, `sampleCode`) are
comma-separated: `?species=124,118&idSource=GSI,PBT`.

### Download variant

Append **`/download`** to any report path
(`/api/reports/scBDWRDNA/download`). It:

- forces `page=all` (no pagination),
- returns the **bare row array**, not the envelope,
- flattens JSONB columns to top-level keys (`attributes` for `projects` /
  `sampleCollections`; `repunit_estimates` for `stockProportionEstimates`) so a
  spreadsheet cell can hold each value.

Used by the frontend's "download current sheet / all sheets" buttons.

### Filter-option lookups

| Path | Returns |
| --- | --- |
| `options/species` | `[{ "id": 124, "value": "CHINOOK" }, …]` |
| `options/idSources` | `["GSI", "PBT", …]` — distinct `individuals.id_source` in use |
| `options/years` | `["2021", "2022", …]` — distinct `inventories.attributes ->> 'Year'` |
| `options/sampleCodes` | `["404", "730", …]` — distinct `inventories.sample_code` |

---

## Response shape

**Report endpoint** (`/api/reports/<name>`):

```json
{
  "data": [ { "…": "one object per row" } ],
  "page": 1,
  "pageSize": 50,
  "total": 673,
  "totalPages": 14
}
```

With `page=all`: `"page": "all"`, `pageSize` = `total` = row count, `totalPages` = 1.

**Download endpoint** (`/api/reports/<name>/download`): just `[ {…}, {…} ]`.

### Type handling

`node-postgres` returned `bigint` and `numeric` as **strings** (to avoid float
precision loss) and JSON/JSONB as **parsed objects**. The frontend relies on
both (React keys, string compares, nested rendering). `sql.py` reproduces this:

- `int8` / `numeric` columns → `str(value)`
- `json` / `jsonb` columns → `json.loads(value)`  *(Django's driver hands these
  back as text from a raw cursor, unlike node-postgres)*
- `int4`, `date`, `bool`, `text` → unchanged

---

## Example

```bash
curl "http://localhost:8000/api/reports/scBDWRDNA?page=1&sort=catch_year&dir=desc&filter=Robertson&species=124&idSource=PBT"
```

```jsonc
{
  "data": [
    {
      "id": "2159",                       // int8 -> string
      "indiv_id": "462_2023_17_12503",
      "species": "CHINOOK",
      "species_id": "124",
      "sex": null,
      "resolved_stock_origin": "ROBERTSON_CREEK",
      "catch_year": 2023,                  // int4 -> number
      "id_source": "PBT",
      "hatchery_origin": "Y",
      "pbt_brood_year": 2019,
      "pbt_brood_collection": "ROBERTSON_CREEK",
      "pbt_brood_group": null,
      "repunit_1": "SWVI", "probability_1": "100.00000",   // numeric -> string
      "repunit_2": null,   "probability_2": null
      // … repunit_3..5
    }
  ],
  "page": 1, "pageSize": 50, "total": 673, "totalPages": 14
}
```

---

## Authentication

Currently **`AllowAny`** — the old public API (`/apiPage`) was unauthenticated
and this keeps that contract. To require a JWT like the rest of the API, edit
one line in [`views.py`](views.py):

```python
from rest_framework.permissions import IsAuthenticated
PERMISSION = [IsAuthenticated]
```

---

## Mapping from the old frontend

| Old (`grd-nextjs`) | New |
| --- | --- |
| `GET /api/scBDWRDNA?…` | `GET /api/reports/scBDWRDNA?…` |
| `GET /api/scBDWRDNA/download?…` | `GET /api/reports/scBDWRDNA/download?…` |
| `GET /api/bsciDNAResults`, `/api/estimateCatchByStockAge`, `/api/stockProportionEstimates` | same, under `/api/reports/` |
| `/api/individuals/download`, `/api/projects/download`, `/api/sampleCollections/download` | `/api/reports/…/download` (paginated version also available now) |
| `lib/queries/species.ts` → `getSpecies()` | `GET /api/reports/options/species` |
| `lib/queries/individuals/idSources.ts` → `getIdSources()` | `GET /api/reports/options/idSources` |
| `lib/queries/collections/years.ts` → `getYears()` | `GET /api/reports/options/years` |
| `lib/queries/collections/sampleCodes.ts` → `getSampleCodes()` | `GET /api/reports/options/sampleCodes` |

The envelope (`data` / `page` / `pageSize` / `total` / `totalPages`) is byte-for-byte
what the old `route.ts` files returned, so frontend components reading
`res.data` / `res.totalPages` need no changes once the URL is updated.

Once every consumer points here, `grd-nextjs/app/api/`, `grd-nextjs/lib/queries/`
and `grd-nextjs/lib/db.ts` can be deleted along with the `pg` dependency.

---

## Adding a report

1. Add an entry to the `REPORTS` dict in [`sql.py`](sql.py):

   ```python
   "myReport": {
       "select": "i.id, spec.value AS species, …",
       "from": CORE_FROM_INDIVIDUALS + " LEFT JOIN … ",
       "kind": "individuals",          # picks the WHERE builder
       # "flatten": "attributes",      # optional: flatten on /download
       # "flatten_always": "some_map", # optional: flatten on every response
   },
   ```

   `kind` is one of `individuals`, `individuals_probability`, `collections`,
   `projects` — it selects which `where_*` builder and which query params apply.

2. Wire the two views + URLs:

   ```python
   # views.py
   my_report, my_report_download = _make_views("myReport")
   ```
   ```python
   # urls.py
   path("myReport", views.my_report),
   path("myReport/download", views.my_report_download),
   ```

No serializer, no model, no migration.
