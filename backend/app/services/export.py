"""LLM-ready context for tables, in English, Arabic or both. Only published content, PII-safe."""

import json

import yaml
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app import i18n
from app.models import Column, DimensionBinding, GlossaryTerm, Metric, Profile, Relationship, SchemaMeta, Table
from app.services.settings_store import get_settings


def _column_doc(session: Session, col: Column, lang: str) -> dict:
    doc: dict = {"name": col.name, "type": col.data_type}
    i18n.put(doc, "display_name", col.display_name, col.display_name_ar, lang)
    i18n.put(doc, "description", col.description, col.description_ar, lang)
    for key in ("role", "semantic_type", "unit", "default_aggregation", "format"):
        if getattr(col, key):
            doc[key] = getattr(col, key)
    if col.non_additive:
        doc["non_additive"] = True
    if col.is_primary_key:
        doc["primary_key"] = True
    if col.deprecated:
        doc["deprecated"] = True
    i18n.put(doc, "synonyms", col.synonyms or None, col.synonyms_ar or None, lang)
    if lang == "ar" and col.synonyms_ar and col.synonyms:
        doc["synonyms"] = [*col.synonyms_ar, *col.synonyms]  # people mix languages when asking
    if col.allowed_values:
        if lang == "ar":
            doc["allowed_values"] = {k: (col.allowed_values_ar or {}).get(k) or v
                                     for k, v in col.allowed_values.items()}
        else:
            doc["allowed_values"] = col.allowed_values
            if lang == "both" and col.allowed_values_ar:
                doc["allowed_values_ar"] = col.allowed_values_ar
    if not col.pii:  # never leak values of PII columns
        examples = list(col.example_values or [])
        if not examples:
            prof = session.scalar(select(Profile).where(Profile.column_id == col.id))
            examples = [t["value"] for t in (prof.top_values if prof else [])][:5]
        if examples:
            doc["example_values"] = examples
    else:
        doc["pii"] = True
    return doc


def table_context(session: Session, table: Table, lang: str = "en", cfg: dict | None = None) -> dict:
    lang = i18n.check_lang(lang)
    cfg = cfg or get_settings(session)
    hide_pii = cfg["pii_columns_in_agent_output"] == "exclude"
    # quarantined columns are awaiting a steward's review and must not reach agents
    cols = [c for c in table.columns if not c.removed and not c.quarantined and not (hide_pii and c.pii)]
    col_ids = [c.id for c in cols]
    rels = session.scalars(
        select(Relationship).where(
            or_(Relationship.from_column_id.in_(col_ids), Relationship.to_column_id.in_(col_ids))
        )
    ).all()
    joins = []
    for r in rels:
        if any(x.removed or x.quarantined or (hide_pii and x.pii) for x in (r.from_column, r.to_column)):
            continue                      # never reveal a join through a hidden or dropped column
        joins.append({
            "join": f"{r.from_column.table.full_name}.{r.from_column.name} = "
                    f"{r.to_column.table.full_name}.{r.to_column.name}",
            "cardinality": r.cardinality,
            "join_type": r.join_type,
            **({"description": r.description} if r.description else {}),
        })
    doc: dict = {"table": table.full_name, "type": table.table_type}
    schema = session.scalar(select(SchemaMeta).where(SchemaMeta.source_id == table.source_id,
                                                     SchemaMeta.name == table.schema_name))
    if schema and (schema.description or schema.description_ar):
        sdoc: dict = {}
        i18n.put(sdoc, "schema_description", schema.description, schema.description_ar, lang)
        doc.update(sdoc)
    i18n.put(doc, "display_name", table.display_name, table.display_name_ar, lang)
    i18n.put(doc, "description", table.description, table.description_ar, lang)
    i18n.put(doc, "grain", table.grain, table.grain_ar, lang)
    for key in ("domain", "owner", "refresh_cadence"):
        if getattr(table, key):
            doc[key] = getattr(table, key)
    i18n.put(doc, "usage_notes", table.usage_notes, table.usage_notes_ar, lang)
    i18n.put(doc, "caveats", table.caveats, table.caveats_ar, lang)
    if table.certified:
        doc["certified"] = True
    if table.partitioned_by:
        doc["partitioned_by"] = table.partitioned_by
    doc["columns"] = [_column_doc(session, c, lang) for c in cols]
    # columns that hold a published dimension's values: say which, and describe each dimension once
    from app.services import dimensions as dim_svc          # (late import: dimensions imports models only)

    bound = {b.column_id: b.dimension for b in session.scalars(
        select(DimensionBinding).where(DimensionBinding.column_id.in_([c.id for c in cols] or [-1])))
        if b.dimension.status == "published"}
    for cdoc, c in zip(doc["columns"], cols):
        if c.id in bound:
            cdoc["dimension"] = bound[c.id].key
    used = list({d.id: d for d in bound.values()}.values())
    if used:
        doc["dimensions"] = [dim_svc.dimension_doc(session, d, lang, compact=True) for d in sorted(used, key=lambda x: x.key)]
    if joins:
        doc["relationships"] = joins
    metrics = session.scalars(
        select(Metric).where(Metric.base_table_id == table.id, Metric.status == "published")
    ).all()
    if metrics:
        out = []
        for m in metrics:
            md: dict = {}
            i18n.put(md, "name", m.name, m.name_ar, lang)
            if lang == "ar" and not m.name_ar:
                md["name"] = m.name
            i18n.put(md, "definition", m.description, m.description_ar, lang)
            md["sql"] = m.sql_expression
            if m.filters:
                md["filters"] = m.filters
            out.append(md)
        doc["metrics"] = out
    return doc


def published_tables(session: Session, domain: str | None = None) -> list[Table]:
    q = select(Table).where(Table.status == "published", Table.removed.is_(False))
    if domain:
        q = q.where(Table.domain == domain)
    return list(session.scalars(q.order_by(Table.schema_name, Table.name)))


def render(docs: list[dict], fmt: str = "yaml", max_tokens: int | None = None) -> str:
    """Render docs; if over budget (≈4 chars/token), drop example values, then secondary detail."""
    def dump(d: list[dict]) -> str:
        if fmt == "json":
            return json.dumps(d, indent=2, ensure_ascii=False)
        return yaml.safe_dump(d, sort_keys=False, allow_unicode=True)

    out = dump(docs)
    if max_tokens and len(out) / 4 > max_tokens:
        for doc in docs:
            for col in doc.get("columns", []):
                col.pop("example_values", None)
        out = dump(docs)
    if max_tokens and len(out) / 4 > max_tokens:
        for doc in docs:
            for key in ("usage_notes", "usage_notes_ar", "caveats", "caveats_ar", "schema_description",
                        "schema_description_ar"):
                doc.pop(key, None)
            for col in doc.get("columns", []):
                for key in ("allowed_values", "allowed_values_ar", "format", "display_name",
                            "display_name_ar"):
                    col.pop(key, None)
        out = dump(docs)
    return out


def glossary_resolve(session: Session, text: str) -> list[GlossaryTerm]:
    """Match a term or synonym in either language, ignoring Arabic diacritics/letter variants."""
    n = i18n.norm(text)
    out = []
    for t in session.scalars(select(GlossaryTerm)):
        names = [t.term, t.term_ar, *(t.synonyms or []), *(t.synonyms_ar or [])]
        if n in {i18n.norm(x) for x in names if x}:
            out.append(t)
    return out
