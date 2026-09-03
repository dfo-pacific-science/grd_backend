"""Raw-SQL report definitions, ported 1:1 from the Next.js `lib/queries/*` layer.

These reports are pivots / JSONB aggregations / full-row text search that the ORM
models poorly, so they run as parameterized raw SQL against the `grd` and
`grd_ref` schemas (resolved via the connection search_path). Behaviour — column
list, joins, filters, sort guard, pagination — matches the original queries.
"""

from __future__ import annotations

import json
import math
import re

from django.db import connection

PAGE_SIZE = 50

# node-postgres returns bigint (int8) and numeric as strings to avoid precision
# loss; the frontend relies on that (React keys, string compares). Match it.
_STRINGIFY_OIDS = {20, 1700}  # int8, numeric
# Django's psycopg3 backend hands back json/jsonb as raw text from a raw cursor
# (unlike node-postgres, which parses it) — decode it here so nested maps/objects
# reach the client as objects.
_JSON_OIDS = {114, 3802}  # json, jsonb

_SAFE_IDENT = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def safe_order_by(sort: str, direction: str) -> str:
    """ORDER BY guard — only a bare identifier passes (no parameterizing column names)."""
    if not sort or not _SAFE_IDENT.match(sort):
        return ""
    return f'ORDER BY "{sort}" {"DESC" if direction == "desc" else "ASC"}'


def _rows(sql: str, params: list) -> list[dict]:
    with connection.cursor() as cur:
        cur.execute(sql, params)
        desc = cur.description
        names = [c.name for c in desc]
        as_str = {i for i, c in enumerate(desc) if c.type_code in _STRINGIFY_OIDS}
        as_json = {i for i, c in enumerate(desc) if c.type_code in _JSON_OIDS}
        out = []
        for row in cur.fetchall():
            d = {}
            for i, value in enumerate(row):
                if value is not None and i in as_json and isinstance(value, str):
                    value = json.loads(value)
                elif value is not None and i in as_str:
                    value = str(value)
                d[names[i]] = value
            out.append(d)
        return out


def _scalar(sql: str, params: list):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# WHERE builders
# ---------------------------------------------------------------------------


def where_individuals(filter_, species, date_from, date_to, id_sources):
    conds, params = [], []
    if filter_:
        params.append(f"%{filter_}%")
        conds.append("i::text ILIKE %s")
    if species:
        params.append(list(species))
        conds.append("p.species_id = ANY(%s::int[])")
    if date_from:
        params.append(date_from)
        conds.append("i.catch_date >= %s")
    if date_to:
        params.append(date_to)
        conds.append("i.catch_date <= %s")
    if id_sources:
        params.append(list(id_sources))
        conds.append("i.id_source = ANY(%s::text[])")
    return (f"WHERE {' AND '.join(conds)}" if conds else ""), params


def where_individuals_with_probability(
    filter_, species, date_from, date_to, id_sources, prob_min, prob_max
):
    where, params = where_individuals(filter_, species, date_from, date_to, id_sources)
    conds = [where[len("WHERE ") :]] if where else []
    if prob_min:
        params.append(prob_min)
        conds.append("irr.probability >= %s")
    if prob_max:
        params.append(prob_max)
        conds.append("irr.probability <= %s")
    return (f"WHERE {' AND '.join(conds)}" if conds else ""), params


def where_collections(filter_, years, sample_codes, filter_column="t"):
    conds, params = [], []
    if filter_:
        params.append(f"%{filter_}%")
        conds.append(f"{filter_column}::text ILIKE %s")
    if years:
        params.append(list(years))
        conds.append("(t.attributes ->> 'Year') = ANY(%s::text[])")
    if sample_codes:
        params.append(list(sample_codes))
        conds.append("t.sample_code = ANY(%s::text[])")
    return (f"WHERE {' AND '.join(conds)}" if conds else ""), params


# ---------------------------------------------------------------------------
# FROM / SELECT fragments
# ---------------------------------------------------------------------------

CORE_FROM_INDIVIDUALS = """
  FROM grd.individuals i
  LEFT JOIN grd.projects p ON p.id = i.projects_id
  LEFT JOIN grd.individuals_inventories ii ON ii.individuals_id = i.id
  LEFT JOIN grd.inventories t ON t.id = ii.inventories_id
  LEFT JOIN grd_ref.species_ref spec ON spec.id = p.species_id
"""

CORE_FROM_COLLECTIONS = " FROM grd.inventories t "

_REPUNIT_PIVOT = """
  LEFT JOIN grd.individuals_pbt ipbt ON ipbt.individuals_id = i.id
  LEFT JOIN (
    SELECT
      individuals_id,
      MAX(repunit)     FILTER (WHERE rn = 1) AS repunit_1,
      MAX(probability) FILTER (WHERE rn = 1) AS probability_1,
      MAX(repunit)     FILTER (WHERE rn = 2) AS repunit_2,
      MAX(probability) FILTER (WHERE rn = 2) AS probability_2,
      MAX(repunit)     FILTER (WHERE rn = 3) AS repunit_3,
      MAX(probability) FILTER (WHERE rn = 3) AS probability_3,
      MAX(repunit)     FILTER (WHERE rn = 4) AS repunit_4,
      MAX(probability) FILTER (WHERE rn = 4) AS probability_4,
      MAX(repunit)     FILTER (WHERE rn = 5) AS repunit_5,
      MAX(probability) FILTER (WHERE rn = 5) AS probability_5
    FROM (
      SELECT individuals_id, repunit, probability,
             ROW_NUMBER() OVER (PARTITION BY individuals_id ORDER BY probability DESC) AS rn
      FROM grd.individuals_repunit_results
    ) ranked
    WHERE rn <= 5
    GROUP BY individuals_id
  ) irr ON irr.individuals_id = i.id
"""

_STOCK_PROPORTION_FROM = """
  LEFT JOIN grd.projects p ON p.id = t.projects_id
  LEFT JOIN (
    SELECT inventories_id, jsonb_object_agg(repunit, jsonb_build_object(
      'point_estimate', point_estimate,
      'standard_deviation', standard_deviation,
      'lower_credible_interval', lower_credible_interval,
      'upper_credible_interval', upper_credible_interval
    )) AS repunit_estimates
    FROM grd.estimates
    WHERE estimates_type = 'REPUNITS'
    GROUP BY inventories_id
  ) re ON re.inventories_id = t.id
"""

# report name -> (select, from, kind)   kind drives which WHERE builder / params apply
REPORTS = {
    "individuals": {
        "select": """
          p.original_filename, i.indiv, i.mgl_pid, i.mgl_pid_batch, i.projects_id,
          spec.value AS species, t.sample_collection, i.catch_year, i.catch_date,
          i.catch_date_2, i.id_source, i.top_collection, i.top_collection_probability,
          sex_id, sex_note
        """,
        "from": CORE_FROM_INDIVIDUALS
        + " LEFT JOIN grd.individuals_extraction ie ON ie.individuals_id = i.id ",
        "kind": "individuals",
    },
    "bsciDNAResults": {
        "select": """
          i.id, i.indiv AS indiv_id, spec.value AS species, spec.id AS species_id,
          i.sex_id AS sex, i.top_collection AS stock_final,
          i.top_collection_probability AS "top_collection_probability(%%)",
          CASE WHEN i.top_collection_probability > 50 THEN i.top_collection ELSE NULL END AS "STOCK_OVER50",
          i.catch_year, i.id_source, t.sample_collection,
          p.original_filename AS analysis_file, p.baseline_file AS baseline
        """,
        "from": CORE_FROM_INDIVIDUALS
        + " LEFT JOIN grd.individuals_pbt ipbt ON ipbt.individuals_id = i.id ",
        "kind": "individuals",
    },
    "scBDWRDNA": {
        "select": """
          i.id, i.indiv AS indiv_id, spec.value AS species, spec.id AS species_id,
          i.sex_id AS sex, i.top_collection AS resolved_stock_origin, i.catch_year,
          i.id_source, CASE WHEN i.id_source = 'PBT' THEN 'Y' ELSE NULL END AS hatchery_origin,
          ipbt.pbt_brood_year, ipbt.pbt_brood_collection, ipbt.pbt_brood_group,
          irr.repunit_1, irr.probability_1, irr.repunit_2, irr.probability_2,
          irr.repunit_3, irr.probability_3, irr.repunit_4, irr.probability_4,
          irr.repunit_5, irr.probability_5
        """,
        "from": CORE_FROM_INDIVIDUALS + _REPUNIT_PIVOT,
        "kind": "individuals",
    },
    "estimateCatchByStockAge": {
        "select": """
          i.id, t.sample_collection, i.indiv AS indiv_id, spec.value AS species,
          i.id_source, irr.repunit, irr.probability
        """,
        "from": CORE_FROM_INDIVIDUALS
        + " LEFT JOIN grd.individuals_repunit_results irr ON irr.individuals_id = i.id "
        + " LEFT JOIN grd.individuals_pbt ipbt ON ipbt.individuals_id = i.id ",
        "kind": "individuals_probability",
    },
    "projects": {
        "select": """
          s.value AS species, p.date_run, p.original_filename AS file_name,
          p.baseline_file, p.attributes
        """,
        "from": " FROM grd.projects p LEFT JOIN grd_ref.species_ref s ON s.id = p.species_id ",
        "kind": "projects",
        "flatten": "attributes",  # applied on /download only
    },
    "sampleCollections": {
        "select": " * ",
        "from": CORE_FROM_COLLECTIONS,
        "kind": "collections",
        "flatten": "attributes",  # applied on /download only
    },
    "stockProportionEstimates": {
        "select": """
          p.id AS project_id, p.baseline_file AS baseline, t.id, t.sample_code,
          t.sample_collection, t.attributes ->> 'Year' AS year,
          t.attributes ->> 'N_reported' AS reported, t.attributes -> 'N_filtered' AS filtered,
          t.contact, re.repunit_estimates
        """,
        "from": CORE_FROM_COLLECTIONS + _STOCK_PROPORTION_FROM,
        "kind": "collections",
        "flatten_always": "repunit_estimates",  # applied on every response
    },
}


def flatten_jsonb_column(rows: list[dict], column: str) -> list[dict]:
    out = []
    for row in rows:
        r = dict(row)
        value = r.pop(column, None)
        if isinstance(value, dict):
            r.update(value)
        out.append(r)
    return out


def run_report(name: str, params: dict, *, download: bool = False):
    """Return either the paginated envelope, or (download=True) the bare row list."""
    spec = REPORTS[name]
    kind = spec["kind"]

    if kind == "individuals":
        where, sql_params = where_individuals(
            params["filter"], params["species"], params["date_from"],
            params["date_to"], params["id_sources"],
        )
    elif kind == "individuals_probability":
        where, sql_params = where_individuals_with_probability(
            params["filter"], params["species"], params["date_from"], params["date_to"],
            params["id_sources"], params["probability_min"], params["probability_max"],
        )
    elif kind == "collections":
        where, sql_params = where_collections(
            params["filter"], params["years"], params["sample_codes"]
        )
    else:  # projects — sort only
        where, sql_params = "", []

    from_sql = spec["from"]
    base_select = f"SELECT {spec['select']} {from_sql}"
    order = safe_order_by(params["sort"], params["dir"])
    flatten_always = spec.get("flatten_always")

    def finish(rows):
        if flatten_always:
            rows = flatten_jsonb_column(rows, flatten_always)
        return rows

    if download or params["page"] == "all":
        rows = finish(_rows(f"{base_select} {where} {order}", sql_params))
        if download and spec.get("flatten"):
            rows = flatten_jsonb_column(rows, spec["flatten"])
        if download:
            return rows
        return {"data": rows, "page": "all", "pageSize": len(rows),
                "total": len(rows), "totalPages": 1}

    page = max(1, params["page"])
    offset = (page - 1) * PAGE_SIZE
    rows = finish(_rows(
        f"{base_select} {where} {order} LIMIT {PAGE_SIZE} OFFSET {offset}", sql_params
    ))
    total = _scalar(f"SELECT COUNT(*) {from_sql} {where}", sql_params)
    return {
        "data": rows,
        "page": page,
        "pageSize": PAGE_SIZE,
        "total": total,
        "totalPages": math.ceil(total / PAGE_SIZE) if total else 0,
    }


# ---------------------------------------------------------------------------
# filter-option lookups
# ---------------------------------------------------------------------------


def option_species():
    return _rows("SELECT id, value FROM grd_ref.species_ref ORDER BY id", [])


def option_id_sources():
    return [
        r["id_source"]
        for r in _rows(
            "SELECT DISTINCT id_source FROM grd.individuals "
            "WHERE id_source IS NOT NULL ORDER BY id_source",
            [],
        )
    ]


def option_years():
    return [
        r["year"]
        for r in _rows(
            "SELECT DISTINCT attributes ->> 'Year' AS year FROM grd.inventories "
            "WHERE attributes ->> 'Year' IS NOT NULL ORDER BY year",
            [],
        )
    ]


def option_sample_codes():
    return [
        r["sample_code"]
        for r in _rows(
            "SELECT DISTINCT sample_code FROM grd.inventories "
            "WHERE sample_code IS NOT NULL ORDER BY sample_code",
            [],
        )
    ]
