"""Dimensions: validation, dependency checks, value resolution and the documents agents receive."""

import re
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import i18n
from app.models import Column, Dimension, DimensionBinding, Table

KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")
ARABIC = re.compile(r"[؀-ۿݐ-ݿ]")
MAX_ALIASES = 100
INLINE_VALUES = 30          # a table's context lists at most this many values per dimension; the rest are looked up


def is_arabic(text: str) -> bool:
    return bool(ARABIC.search(text))


def word_key(text: str | None) -> str:
    """How two words are compared: case, Arabic diacritics/letter variants, spacing and edge punctuation ignored."""
    t = re.sub(r"\s+", " ", i18n.norm(text))
    return t.strip(" .,;:?!\"'()[]{}،؛؟")


def clean_words(words: list[str] | None, limit: int = MAX_ALIASES) -> list[str]:
    """Trim, drop blanks and duplicates (by comparison key), keep order."""
    out, seen = [], set()
    for w in words or []:
        w = re.sub(r"\s+", " ", (w or "").strip())[:120]
        k = word_key(w)
        if k and k not in seen:
            seen.add(k)
            out.append(w)
    return out[:limit]


def name_of(d: Dimension, lang: str = "en") -> str:
    return (d.label_ar or d.label or d.key) if lang == "ar" else (d.label or d.key)


def label_of(v, lang: str) -> str | None:
    if lang == "ar":
        return v.label_ar or v.label
    if lang == "both":
        return v.label or v.label_ar
    return v.label


def universe(session: Session, dim: Dimension) -> list[Dimension]:
    """The dimensions `dim` is judged against: every live one (not draft copies), with `dim` itself in its own place."""
    live = session.scalars(select(Dimension).where(Dimension.draft_of_id.is_(None), Dimension.key != dim.key)).all()
    return [*live, dim]


# --------------------------------------------------------------------------- validation
def check(session: Session, dim: Dimension) -> list[dict]:
    """Everything wrong or doubtful about a dimension. `error` blocks saving/publishing; `warning` is advice."""
    issues: list[dict] = []

    def add(severity, code, message, **extra):
        issues.append({"severity": severity, "code": code, "message": message, **extra})

    mine = {v.value for v in dim.values}
    seen_terms: set[str] = set()
    for f in dim.families or []:
        term = (f.get("term") or "").strip()
        if not term:
            add("error", "family_term", "Every family needs a term")
            continue
        k = word_key(term)
        if k in seen_terms:
            add("error", "family_duplicate", f"The family “{term}” is listed twice", term=term)
        seen_terms.add(k)
        vals = list(dict.fromkeys(f.get("values") or []))
        if len(vals) < 2:
            add("error", "family_size", f"The family “{term}” needs at least two values", term=term)
        for v in vals:
            if v not in mine:
                add("error", "family_unknown_value",
                    f"The family “{term}” uses “{v}”, which is not a value of {dim.key}", term=term, value=v)

    others = {d.key: d for d in universe(session, dim)}
    for c in dim.applies_to or []:
        ref = others.get(c.get("dimension"))
        if ref is None:
            add("error", "applies_unknown_dimension", f"“applies to” refers to the unknown dimension “{c.get('dimension')}”")
            continue
        listed = {v.value for v in ref.values}
        vals = c.get("values") or []
        if not vals:
            add("error", "applies_empty", f"“applies to” {ref.key} needs at least one value")
        for v in vals:
            if v not in listed:
                add("error", "applies_unknown_value", f"“applies to” uses “{v}”, which is not a value of {ref.key}", value=v)
        if ref.key != dim.key and any(x.get("dimension") == dim.key for x in ref.applies_to or []):
            add("warning", "applies_circular", f"{dim.key} and {ref.key} restrict each other, so neither is a clear population")

    # words that can mean more than one value make a question ambiguous
    owners: dict[str, set[str]] = defaultdict(set)
    shown: dict[str, str] = {}
    for v in dim.values:
        for w in (v.value, v.label, v.label_ar, *(v.aliases or [])):
            k = word_key(w)
            if k:
                owners[k].add(v.value)
                shown.setdefault(k, w)
    for k, vals in owners.items():
        if len(vals) > 1:
            add("warning", "ambiguous_word", f"“{shown[k]}” can mean {', '.join(sorted(vals))}; a question using it is ambiguous",
                word=shown[k], values=sorted(vals))
    for f in dim.families or []:
        k = word_key(f.get("term"))
        if k in owners:
            add("warning", "family_word_collides", f"The family “{f.get('term')}” is also a single value’s name",
                term=f.get("term"))

    for b in dim.bindings:
        if b.column.removed:
            add("warning", "dropped_column", f"{b.column.table.full_name}.{b.column.name} was dropped from the lake",
                column_id=b.column_id)
    return issues


def errors(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["severity"] == "error"]


def value_dependents(session: Session, dim: Dimension, value: str) -> dict:
    """What would break if `value` were removed."""
    v = next((x for x in dim.values if x.value == value), None)
    fam = [f.get("term") for f in dim.families or [] if value in (f.get("values") or [])]
    applies = []
    for d in universe(session, dim):
        if any(c.get("dimension") == dim.key and value in (c.get("values") or []) for c in d.applies_to or []):
            applies.append({"dimension": d.key, "own": d.id == dim.id})
    return {"aliases": len(v.aliases or []) if v else 0, "families": fam, "applies_to": applies}


# --------------------------------------------------------------------------- "applies to" guidance
def applies_doc(session: Session, dim: Dimension, lang: str = "en") -> dict:
    conds = dim.applies_to or []
    if not conds:
        return {"everyone": True}
    by_key = {d.key: d for d in universe(session, dim)}
    parts_en, parts_ar, structured = [], [], []
    for c in conds:
        ref = by_key.get(c.get("dimension"))
        vals = list(c.get("values") or [])
        structured.append({"dimension": c.get("dimension"), "values": vals})
        # the condition names the dimension by its key (what tools use); the subject below uses its readable name
        parts_en.append(f"{c.get('dimension')} = {', '.join(vals)}")
        parts_ar.append(f"{c.get('dimension')} = {'، '.join(vals)}")
    en = (f"When breaking down or counting by {name_of(dim, 'en')}, restrict the data to {' AND '.join(parts_en)}. "
          "Measure shares against that restricted population.")
    ar = (f"عند التجميع أو العدّ حسب «{name_of(dim, 'ar')}»، قيّد البيانات على: {' و '.join(parts_ar)}. "
          "واحسب النسب مقابل هذه الفئة المقيَّدة فقط.")
    out: dict = {"everyone": False, "conditions": structured}
    if lang == "ar":
        out["instruction"] = ar + (f" {dim.applies_note_ar}" if dim.applies_note_ar else (f" {dim.applies_note}" if dim.applies_note else ""))
    elif lang == "both":
        out["instruction"] = en + (f" {dim.applies_note}" if dim.applies_note else "")
        out["instruction_ar"] = ar + (f" {dim.applies_note_ar}" if dim.applies_note_ar else "")
    else:
        out["instruction"] = en + (f" {dim.applies_note}" if dim.applies_note else "")
    return out


# --------------------------------------------------------------------------- what agents may see
def live_bound_columns(dim: Dimension) -> list[Column]:
    """Bound columns an agent can actually see: live, not hidden, on a published table."""
    return [b.column for b in dim.bindings
            if not b.column.removed and not b.column.quarantined
            and b.column.table.status == "published" and not b.column.table.removed]


def visible_dimensions(session: Session, domains: list | None) -> list[Dimension]:
    """Published dimensions; a domain-restricted key only gets those bound to a column in its domains."""
    dims = session.scalars(select(Dimension).where(Dimension.status == "published", Dimension.draft_of_id.is_(None)).order_by(Dimension.key)).all()
    if domains is None:
        return list(dims)
    return [d for d in dims if any(c.table.domain in domains for c in live_bound_columns(d))]


def split_aliases(aliases: list[str]) -> tuple[list[str], list[str]]:
    en = [a for a in aliases if not is_arabic(a)]
    ar = [a for a in aliases if is_arabic(a)]
    return en, ar


def dimension_doc(session: Session, dim: Dimension, lang: str = "en", compact: bool = False) -> dict:
    """The agent-facing description. `compact` (used inside a table's context) omits aliases and caps the value list."""
    lang = i18n.check_lang(lang)
    doc: dict = {"key": dim.key}
    i18n.put(doc, "label", dim.label, dim.label_ar, lang)
    i18n.put(doc, "description", dim.description, dim.description_ar, lang)
    if not compact:
        syn_en, syn_ar = clean_words(dim.synonyms), clean_words(dim.synonyms_ar)
        if lang == "ar":
            if syn_ar or syn_en:
                doc["synonyms"] = [*syn_ar, *syn_en]
        else:
            i18n.put(doc, "synonyms", syn_en or None, syn_ar or None, lang)
    values = []
    for v in dim.values:
        item: dict = {"value": v.value}
        lab = label_of(v, lang)
        if lab:
            item["label"] = lab
        if lang == "both" and v.label_ar:
            item["label_ar"] = v.label_ar
        if not compact:
            en, ar = split_aliases(v.aliases or [])
            if lang == "ar":
                if ar or en:
                    item["aliases"] = [*ar, *en]
            else:
                if en:
                    item["aliases"] = en
                if lang == "both" and ar:
                    item["aliases_ar"] = ar
        values.append(item)
    total = len(values)
    doc["values"] = values[:INLINE_VALUES] if compact else values
    if compact and total > INLINE_VALUES:
        doc["values_total"] = total
        doc["note"] = "Only some values are listed; use resolve_value or describe_dimension for the full vocabulary."
    if dim.families and not compact:
        fams = []
        for f in dim.families:
            item = {"term": f.get("term"), "values": f.get("values")}
            if f.get("term_ar") and lang in ("ar", "both"):
                item["term_ar"] = f["term_ar"]
            fams.append(item)
        doc["families"] = fams
    doc["applies_to"] = applies_doc(session, dim, lang)
    if not compact:
        doc["columns"] = [f"{c.table.full_name}.{c.name}" for c in live_bound_columns(dim)]
    return doc


def dimension_summary(dim: Dimension, lang: str = "en") -> dict:
    out: dict = {"key": dim.key}
    i18n.put(out, "label", dim.label, dim.label_ar, lang)
    i18n.put(out, "description", dim.description, dim.description_ar, lang)
    out["values"] = len(dim.values)
    return out


# --------------------------------------------------------------------------- resolving words to stored values
def resolve(dims: list[Dimension], text: str, dimension_key: str | None = None, lang: str = "en") -> dict:
    """Turn what someone said ("citizens", "مقيمين") into stored values, and spot dimension names."""
    k = word_key(text)
    matches: list[dict] = []
    named: list[dict] = []
    if k:
        for d in dims:
            if dimension_key and d.key != dimension_key:
                continue
            names = [d.key.replace("_", " "), d.key, d.label, d.label_ar, *(d.synonyms or []), *(d.synonyms_ar or [])]
            if any(word_key(n) == k for n in names if n):
                named.append({"dimension": d.key, "label": name_of(d, lang)})
            by_value = {v.value: v for v in d.values}
            for v in d.values:
                for via, w in (("value", v.value), ("label", v.label), ("label", v.label_ar),
                               *(("alias", a) for a in v.aliases or [])):
                    if w and word_key(w) == k:
                        matches.append({"dimension": d.key, "value": v.value, "label": label_of(v, lang), "via": via})
                        break
            for f in d.families or []:
                if k in (word_key(f.get("term")), word_key(f.get("term_ar"))):
                    for val in f.get("values") or []:
                        v = by_value.get(val)
                        matches.append({"dimension": d.key, "value": val, "label": label_of(v, lang) if v else None,
                                        "via": "family", "family": f.get("term")})
    singles = {(m["dimension"], m["value"]) for m in matches if m["via"] != "family"}
    families = {(m["dimension"], m.get("family")) for m in matches if m["via"] == "family"}
    ambiguous = len(singles) + len(families) > 1
    return {"query": text, "matches": matches, "dimensions": named, "ambiguous": ambiguous}
