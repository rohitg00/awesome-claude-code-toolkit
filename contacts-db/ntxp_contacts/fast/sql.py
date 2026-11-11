"""Generate the vectorized DuckDB normalization SQL from a SourceMapping.

jevt's "query builders": one SELECT normalizes every field set-based — phones to
E.164, emails lowercased, ZIP repaired, float-IDs stripped, name/org names
normalized, plus a content hash and dedup key — instead of per-row Python.
"""
from __future__ import annotations

from .mapping import SourceMapping

MAX_PHONES = 4
_NAME_SUFFIX = r"\b(jr|sr|ii|iii|iv|v|mr|mrs|ms|dr|miss|prof)\b"
_ORG_SUFFIX = (r"\b(inc|incorporated|llc|l l c|ltd|limited|co|corp|corporation|company|"
               r"lp|llp|pllc|pc|the|and|group|holdings|enterprises|services|service)\b")


def _raw(col: str | None) -> str:
    return f'"{col}"' if col else "CAST(NULL AS VARCHAR)"


def _email(expr: str) -> str:
    return (f"NULLIF(lower(trim(regexp_replace({expr}, 'mailto:', '', 'g'))), '')")


def _phone_e164(expr: str) -> str:
    d = f"regexp_replace(COALESCE({expr}, ''), '[^0-9]', '', 'g')"
    return (f"CASE WHEN length({d}) = 10 THEN '+1' || {d} "
            f"WHEN length({d}) = 11 AND left({d},1) = '1' THEN '+' || {d} ELSE NULL END")


def _zip5(expr: str) -> str:
    d = f"regexp_replace(COALESCE({expr}, ''), '[^0-9]', '', 'g')"
    return f"NULLIF(lpad(left({d}, 5), 5, '0'), '00000')"


def _state(expr: str) -> str:
    u = f"upper(trim(COALESCE({expr}, '')))"
    return f"CASE WHEN length({u}) = 2 THEN {u} ELSE NULL END"


def _strip_float_id(expr: str) -> str:
    return f"regexp_replace(COALESCE({expr}, ''), '\\.0+$', '')"


def _collapse(expr: str) -> str:
    return f"trim(regexp_replace({expr}, '\\s+', ' ', 'g'))"


def _name_norm(full_expr: str) -> str:
    base = f"lower(COALESCE({full_expr}, ''))"
    nopunct = f"regexp_replace({base}, '[^a-z0-9 ]', ' ', 'g')"
    nosuffix = f"regexp_replace({nopunct}, '{_NAME_SUFFIX}', ' ', 'g')"
    return f"NULLIF({_collapse(nosuffix)}, '')"


def _org_norm(expr: str) -> str:
    base = f"lower(COALESCE({expr}, ''))"
    nopunct = f"regexp_replace({base}, '[^a-z0-9 ]', ' ', 'g')"
    nosuffix = f"regexp_replace({nopunct}, '{_ORG_SUFFIX}', ' ', 'g')"
    return f"NULLIF({_collapse(nosuffix)}, '')"


def build_normalize_sql(m: SourceMapping, relation: str) -> str:
    """Return a SELECT over `relation` producing fixed canonical columns."""
    # names
    if m.contact_full:
        full = _raw(m.contact_full)
        first = f"regexp_replace(trim(split_part({full}, ' ', 1)), '[^a-zA-Z]', '', 'g')"
        last = f"trim(regexp_replace({full}, '^\\S+\\s*', ''))"
    else:
        first = f"trim({_raw(m.first_name)})"
        last = f"trim({_raw(m.last_name)})"
        full = f"NULLIF(trim(COALESCE({first},'') || ' ' || COALESCE({last},'')), '')"
    name_norm = _name_norm(full)
    block = (f"NULLIF(lower(regexp_replace(COALESCE(NULLIF({last},''), "
             f"regexp_extract({name_norm}, '(\\w+)$', 1)), '[^a-zA-Z]', '', 'g')), '') "
             f"|| '|' || left(lower(COALESCE(NULLIF({first},''), split_part({name_norm}, ' ', 1))), 1)")

    org_norm = _org_norm(_raw(m.org_name))
    email_norm = _email(_raw(m.email))
    email_invalid = ("1" if False else
                     (f"CASE WHEN lower(COALESCE({_raw(m.email_invalid)},'')) "
                      f"IN ('yes','true','1','x') THEN 1 ELSE 0 END"))

    # phones (fixed slots) — keep exprs so they can be inlined into the hash
    phone_e164 = []
    phone_cols = []
    for i in range(MAX_PHONES):
        if i < len(m.phones):
            col, kind = m.phones[i]
            e164 = _phone_e164(_raw(col))
            phone_e164.append(e164)
            phone_cols.append(f"{_raw(col)} AS p{i}_raw")
            phone_cols.append(f"{e164} AS p{i}_e164")
            phone_cols.append(f"'{kind}' AS p{i}_kind")
        else:
            phone_e164.append("NULL")
            phone_cols.append(f"CAST(NULL AS VARCHAR) AS p{i}_raw")
            phone_cols.append(f"CAST(NULL AS VARCHAR) AS p{i}_e164")
            phone_cols.append(f"CAST(NULL AS VARCHAR) AS p{i}_kind")

    # address
    line1 = f"NULLIF(trim({_raw(m.line1)}), '')"
    city = f"NULLIF(trim({_raw(m.city)}), '')"
    state = _state(_raw(m.state))
    zip5 = _zip5(_raw(m.zip))
    addr_norm = _collapse(
        f"lower(regexp_replace(concat_ws(' ', {line1}, {city}, {state}, {zip5}), '[^a-z0-9 ]', ' ', 'g'))")

    # certs: concat the cert columns, comma-joined
    cert = ("concat_ws(',', " + ", ".join(_raw(c) for c in m.cert_columns) + ")") \
        if m.cert_columns else "CAST(NULL AS VARCHAR)"

    # source_pk from mapped parts (canonical names resolve to exprs; else raw col, float-stripped)
    canon = {"org_name_norm": org_norm, "name_norm": name_norm, "email_norm": email_norm}
    pk_parts = [canon.get(p, _strip_float_id(_raw(p))) for p in m.source_pk_parts]
    source_pk = f"NULLIF(concat_ws('|', {', '.join(pk_parts)}), '')" if pk_parts else "CAST(NULL AS VARCHAR)"

    # content hash + dedup key — inline exprs (no alias references), one flat SELECT
    row_hash = (f"md5(concat_ws('~', COALESCE({org_norm},''), COALESCE({name_norm},''), "
                f"COALESCE(trim({_raw(m.title)}),''), COALESCE({email_norm},''), "
                f"COALESCE({phone_e164[0]},''), COALESCE({phone_e164[1]},''), "
                f"COALESCE({addr_norm},''), COALESCE({cert},'')))")
    ckey = f"COALESCE({email_norm}, {name_norm} || '|' || COALESCE({org_norm},''))"

    return f"""
      SELECT
        NULLIF(trim({_raw(m.org_name)}), '') AS org_name,
        {org_norm}      AS org_name_norm,
        NULLIF(trim({_raw(m.website)}), '')   AS website,
        NULLIF(trim({_raw(m.license_no)}), '') AS license_no,
        NULLIF({first}, '') AS first_name,
        NULLIF({last}, '')  AS last_name,
        {full}          AS full_name,
        {name_norm}     AS name_norm,
        {block}         AS block_key,
        NULLIF(trim({_raw(m.title)}), '') AS title,
        {email_norm}    AS email_norm,
        {email_invalid} AS email_invalid,
        {line1} AS line1, {city} AS city, {state} AS state, {zip5} AS zip,
        {addr_norm}     AS addr_norm,
        NULLIF(trim({_raw(m.region)}), '')       AS region,
        NULLIF(trim({_raw(m.contact_type)}), '') AS contact_type,
        {cert}          AS cert_raw,
        {', '.join(phone_cols)},
        {source_pk}     AS source_pk,
        {row_hash}      AS row_hash,
        {ckey}          AS ckey
      FROM {relation}
      WHERE {org_norm} IS NOT NULL OR {name_norm} IS NOT NULL
    """

