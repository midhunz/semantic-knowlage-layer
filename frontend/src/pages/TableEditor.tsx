import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, send } from "../api";
import { useAuth } from "../auth";
import { ArrowLeft, Shapes, Bot, Check, CheckCheck, ChevronDown, ChevronRight, Columns, Cpu, Eye, EyeOff, FileText, GitPullRequestDraft, History as HistoryIcon, Key, Send, ShieldAlert, ShieldCheck, Sparkles, Table2, Wand2, ChevronsDownUp, ChevronsUpDown, Copy, SearchX } from "lucide-react";
import { HistoryPanel, PublishDialog } from "../revisions";
import { Bi, Cov, EmptyState, RoleChip, SearchInput, Select, StatusChip, Text, csv, useLang, useTitle, useToast } from "../ui";

const TABLE_TYPES = ["", "fact", "dimension", "bridge", "staging", "aggregate"];
const ROLES = ["", "identifier", "dimension", "measure", "time", "attribute"];
const AGGS = ["", "sum", "avg", "min", "max", "count", "none"];

const kvText = (v: Record<string, string> | null) => Object.entries(v ?? {}).map(([k, m]) => `${k}=${m}`).join("; ");
const textKv = (v: string) =>
  Object.fromEntries(v.split(";").map((s) => s.split("=").map((x) => x.trim())).filter((kv) => kv[0] && kv[1]));
const SHARED = ["description", "description_ar", "display_name", "display_name_ar", "role", "semantic_type", "unit", "default_aggregation", "synonyms", "synonyms_ar"];

function ColumnRow({ c, tableId, open, onToggle }: { c: any; tableId: string; open: boolean; onToggle: () => void }) {
  const { canEdit } = useAuth();
  const qc = useQueryClient();
  const toast = useToast();
  const refresh = () => ["table", "tables", "catalog", "stats", "tree", "colgroups", "revision", "pendingq", "quarantine"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  const save = useMutation({
    mutationFn: (patch: object) => send("PATCH", `/api/columns/${c.id}`, patch),
    onSuccess: (r: any) => { refresh(); if (r.staged) toast("Saved as a pending change — agents see it after you publish"); },
    onError: (e) => toast(`Could not save: ${(e as Error).message}`, true),
  });
  const p = (patch: object) => save.mutate(patch);
  const staged = (...fields: string[]) => fields.some((f) => (c.staged_fields ?? []).includes(f));
  const applyAll = useMutation({
    mutationFn: () => send("POST", "/api/catalog/column-groups/apply", {
      name: c.name, only_empty: true,
      patch: Object.fromEntries(SHARED.filter((k) => c[k] && !(Array.isArray(c[k]) && !c[k].length)).map((k) => [k, c[k]])),
    }),
    onSuccess: (r: any) => { toast(`Filled ${r.updated} other columns named ${c.name} across ${r.tables} tables`); refresh(); },
    onError: (e) => toast(String(e), true),
  });
  const flag = (key: string, label: string) => (
    <label className="check-inline"><input type="checkbox" disabled={!canEdit} checked={!!c[key]} onChange={(e) => p({ [key]: e.target.checked })} /> {label}</label>
  );
  const has = (k: string) => !!c[k];
  return (
    <div className={`col-row${c.removed ? " removed" : ""}`}>
      <div className="sum" onClick={onToggle} role="button" tabIndex={0} aria-expanded={open}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onToggle())}>
        <span className="col-name" title={c.name}>{c.name}{c.needs_review && !c.removed && <i className="rv-dot" title="Needs review" />}{(c.staged_fields ?? []).length > 0 && <i className="pend-dot" title="Has unpublished changes" />}</span>
        <span className="col-type" title={c.data_type}>{c.data_type}</span>
        <span className="role">{c.role ? <RoleChip role={c.role} /> : <span className="muted">—</span>}
          {c.is_primary_key && <span className="chip gold with-ic" style={{ marginInlineStart: 4 }}><Key className="ic" />PK</span>}
          {c.pii && <span className="chip warn with-ic" style={{ marginInlineStart: 4 }}><ShieldAlert className="ic" />PII</span>}
          {c.removed && <span className="chip warn" style={{ marginInlineStart: 4 }}>dropped</span>}
          {c.dimension && <Link className="chip gold-soft with-ic" style={{ marginInlineStart: 4 }} to={`/dimensions/${c.dimension.id}`} onClick={(e) => e.stopPropagation()} title={`Holds the values of the dimension “${c.dimension.key}”`}><Shapes className="ic" />{c.dimension.label}</Link>}
          {c.quarantined && !c.removed && <span className="chip hold with-ic" style={{ marginInlineStart: 4 }} title={c.quarantine_reason ?? "Hidden from agents"}><EyeOff className="ic" />Hidden</span>}</span>
        <span className={`desc${c.description || c.description_ar ? "" : " none"}`} dir="auto">{c.description || c.description_ar || "No description yet"}</span>
        <span className="badges" title="Documented in English / Arabic">
          <span className={`bdg en${has("description") ? " on" : ""}`}>EN</span>
          <span className={`bdg ar${has("description_ar") ? " on" : ""}`}>AR</span>
        </span>
        {open ? <ChevronDown className="chev" aria-hidden /> : <ChevronRight className="chev" aria-hidden />}
      </div>
      {open && (
        <div className="body">
          {c.quarantined && !c.removed && (
            <div className="qbanner" style={{ marginTop: 12 }}>
              <EyeOff className="ic" /><span><b>Hidden from agents.</b> {c.quarantine_reason}. Agents will not see this column until it is released.</span>
              <span className="spacer" />
              {canEdit && <>
                <button className="btn" onClick={() => p({ quarantined: false, needs_review: false })}><Eye className="ic" />Release</button>
                <button className="btn" onClick={() => p({ quarantined: false, needs_review: false, pii: true })}><ShieldCheck className="ic" />Release as personal data</button>
              </>}
            </div>
          )}
          <div className="fields" style={{ marginTop: 12 }}>
            <Bi label="Display name" stagedEn={staged("display_name")} stagedAr={staged("display_name_ar")} en={c.display_name ?? ""} ar={c.display_name_ar ?? ""} onEn={(v) => p({ display_name: v || null })} onAr={(v) => p({ display_name_ar: v || null })} />
            <Bi label="Description" area stagedEn={staged("description")} stagedAr={staged("description_ar")} en={c.description ?? ""} ar={c.description_ar ?? ""} onEn={(v) => p({ description: v || null })} onAr={(v) => p({ description_ar: v || null })} />
            <div className="three-col">
              <Select label="Role" staged={staged("role")} value={c.role ?? ""} options={ROLES} onSave={(v) => p({ role: v || null })} />
              <Select label="Default aggregation" staged={staged("default_aggregation")} value={c.default_aggregation ?? ""} options={AGGS} onSave={(v) => p({ default_aggregation: v || null })} />
              <Text label="Semantic type" staged={staged("semantic_type")} value={c.semantic_type ?? ""} onSave={(v) => p({ semantic_type: v || null })} />
            </div>
            <div className="two-col">
              <Text label="Synonyms · EN (comma separated)" staged={staged("synonyms")} value={(c.synonyms ?? []).join(", ")} onSave={(v) => p({ synonyms: csv(v) })} />
              <Text rtl label="مرادفات · عربي (مفصولة بفاصلة)" staged={staged("synonyms_ar")} value={(c.synonyms_ar ?? []).join("، ")} onSave={(v) => p({ synonyms_ar: csv(v) })} />
            </div>
            <div className="two-col">
              <Text label="Allowed values · EN (code=meaning; …)" staged={staged("allowed_values")} value={kvText(c.allowed_values)} onSave={(v) => p({ allowed_values: textKv(v) })} />
              <Text rtl label="القيم المسموحة · عربي (الرمز=المعنى; …)" staged={staged("allowed_values_ar")} value={kvText(c.allowed_values_ar)} onSave={(v) => p({ allowed_values_ar: textKv(v) })} />
            </div>
            <div className="three-col">
              <Text label="Unit" staged={staged("unit")} value={c.unit ?? ""} onSave={(v) => p({ unit: v || null })} />
              <div className="field"><label>Flags</label><div style={{ display: "flex", gap: 14, flexWrap: "wrap", paddingTop: 6 }}>{flag("is_primary_key", "Primary key")}{flag("pii", "PII")}{flag("deprecated", "Deprecated")}{flag("non_additive", "Non-additive")}{flag("quarantined", "Hidden from agents")}{c.needs_review && flag("needs_review", "Needs review")}</div></div>
            </div>
          </div>
          {canEdit && <div className="apply-all">
            <button className="btn" disabled={applyAll.isPending || !(c.description || c.description_ar)} onClick={() => applyAll.mutate()}><Copy className="ic" />Use this definition for every column named “{c.name}”</button>
            <span className="muted">Fills only blanks in other tables — nothing already written is changed.</span>
          </div>}
        </div>
      )}
    </div>
  );
}

const TABS = [["overview", "Overview", FileText], ["columns", "Columns", Columns], ["history", "History", HistoryIcon], ["preview", "Agent preview", Bot], ["tech", "Technical", Cpu]] as const;
type Tab = (typeof TABS)[number][0];

export default function TableEditor() {
  const { id = "" } = useParams();
  const qc = useQueryClient();
  const toast = useToast();
  const { lang } = useLang();
  const { canEdit } = useAuth();
  const [sp, setSp] = useSearchParams();
  const tab = ((sp.get("tab") as Tab) || "overview") as Tab;
  const setTab = (t: Tab) => setSp(new URLSearchParams(t === "overview" ? {} : { tab: t }), { replace: true });
  const { data: t, isLoading } = useQuery({ queryKey: ["table", id], queryFn: () => api(`/api/tables/${id}`) });
  const [open, setOpen] = useState<Set<number>>(new Set());
  const [cq, setCq] = useState("");
  const [only, setOnly] = useState<"" | "undocumented" | "no_arabic" | "review" | "hidden">("");
  const [reviewing, setReviewing] = useState(false);

  const refresh = () => ["table", "catalog", "stats", "tree", "facets", "revision", "history", "pendingq", "quarantine"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  const save = useMutation({
    mutationFn: (patch: object) => send("PATCH", `/api/tables/${id}`, patch),
    onSuccess: (r: any) => { refresh(); if (r.staged) toast("Saved as a pending change — agents see it after you publish"); },
    onError: (e) => toast(`Could not save: ${String((e as Error).message)}`, true),
  });
  const releaseAll = useMutation({
    mutationFn: (mark_pii: boolean) => send("POST", "/api/catalog/quarantine/release", { ids: t.columns.filter((c: any) => c.quarantined && !c.removed).map((c: any) => c.id), mark_pii }),
    onSuccess: (r: any) => { refresh(); toast(`Released ${r.released} column${r.released === 1 ? "" : "s"} to agents`); },
    onError: (e) => toast(String((e as Error).message), true),
  });
  const previewLang = lang === "ar" ? "ar" : lang === "both" ? "both" : "en";
  const columnsKey = t ? JSON.stringify(t.columns.map((c: any) => [c.id, c.description, c.description_ar, c.role])) : "";
  const preview = useQuery({
    queryKey: ["preview", id, previewLang, t?.status, columnsKey, t?.description, t?.description_ar, t?.grain, t?.grain_ar],
    enabled: t?.status === "published" && tab === "preview",
    queryFn: () => fetch(`/agent/tables/${t.full_name}/context?lang=${previewLang}`).then((r) => r.text()),
  });

  const cols: any[] = useMemo(() => {
    if (!t) return [];
    const n = cq.trim().toLowerCase();
    return t.columns.filter((c: any) => {
      if (n && !`${c.name} ${c.description ?? ""} ${c.description_ar ?? ""} ${(c.synonyms ?? []).join(" ")} ${(c.synonyms_ar ?? []).join(" ")}`.toLowerCase().includes(n)) return false;
      if (only === "undocumented") return !c.removed && !c.description;
      if (only === "no_arabic") return !c.removed && !c.description_ar;
      if (only === "review") return c.needs_review;
      if (only === "hidden") return c.quarantined && !c.removed;
      return true;
    });
  }, [t, cq, only]);

  useTitle(t ? (t.display_name || t.name) : "Table");
  if (isLoading) return <div className="loading">Loading table…</div>;
  if (!t) return <div className="loading">Table not found.</div>;
  const p = (patch: object) => save.mutate(patch);
  const live = t.columns.filter((c: any) => !c.removed).length;
  const undocumented = t.columns.filter((c: any) => !c.removed && !c.description).length;
  const pend = t.pending;
  const stagedT = (...f: string[]) => f.some((x) => (pend?.table_fields ?? []).includes(x));
  const tabs = TABS.filter(([k]) => k !== "history" || t.version > 0 || t.status === "published");
  const toggle = (cid: number) => setOpen((s) => { const n = new Set(s); n.has(cid) ? n.delete(cid) : n.add(cid); return n; });
  const biT = (label: string, k: string, area?: boolean) => (
    <Bi label={label} area={area} stagedEn={stagedT(k)} stagedAr={stagedT(`${k}_ar`)} en={t[k] ?? ""} ar={t[`${k}_ar`] ?? ""} onEn={(v) => p({ [k]: v || null })} onAr={(v) => p({ [`${k}_ar`]: v || null })} />
  );

  return (
    <div>
      <div className="te-head">
        <div className="te-head-inner wide">
          <div className="sub" style={{ marginBottom: 4 }}><Link className="crumb es-inline" to={`/catalog?source_id=${t.source_id}&schema=${encodeURIComponent(t.schema_name)}`}><ArrowLeft className="ic" />{t.source} / {t.schema_name}</Link></div>
          <div className="d-head">
            <div style={{ minWidth: 0 }}>
              <div className="d-kind"><Table2 className="ic" />{t.table_type ?? "table"}{t.domain ? ` · ${t.domain}` : ""}</div>
              <div className="d-title">{t.display_name || t.name}{t.display_name_ar && <span className="ar-text" dir="rtl" style={{ marginLeft: 14, fontWeight: 500 }}>{t.display_name_ar}</span>}</div>
              <div className="d-name">{t.full_name}</div>
            </div>
            {canEdit && <div className="d-actions">
              {t.status === "draft" && <button className="btn" onClick={() => p({ status: "reviewed", needs_review: false })}><CheckCheck className="ic" />Mark reviewed</button>}
              {t.status !== "published"
                ? <button className="btn primary" onClick={() => p({ status: "published", needs_review: false })}><Send className="ic" />Publish to agents</button>
                : <button className="btn" onClick={() => (!pend || window.confirm("This table has pending changes. Unpublishing applies them (agents will not see the table meanwhile). Continue?")) && p({ status: "draft" })}><EyeOff className="ic" />Unpublish</button>}
            </div>}
          </div>
          <div className="chips" style={{ alignItems: "center" }}>
            <StatusChip status={t.status} />
            {t.needs_review && <span className="chip review">needs review</span>}
            {t.certified && <span className="chip gold">certified</span>}
            {t.removed && <span className="chip warn">dropped from lake</span>}
            {t.version > 0 && <span className="chip" title="Latest published version">v{t.version}</span>}
            {pend && <span className="chip gold-soft with-ic"><GitPullRequestDraft className="ic" />{pend.count} unpublished</span>}
            {t.quarantined_count > 0 && <span className="chip hold with-ic"><EyeOff className="ic" />{t.quarantined_count} hidden</span>}
            <span className="chip">{live} columns</span>
            {t.row_count != null && <span className="chip">{t.row_count.toLocaleString()} rows</span>}
            <span style={{ flex: 1 }} />
            <div style={{ width: 260 }}><Cov en={t.completeness} ar={t.completeness_ar} /></div>
          </div>
          <div className="tabs" role="tablist">
            {tabs.map(([k, label, Icon]) => (
              <button key={k} role="tab" aria-selected={tab === k} className={`tab${tab === k ? " on" : ""}`} onClick={() => setTab(k)}>
                <Icon className="ic" />{label}{k === "columns" && <span className="count-pill">{live}</span>}
                {k === "columns" && undocumented > 0 && <span className="rv-dot" title={`${undocumented} without a description`} />}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="te-body wide">
        {pend && (
          <div className="pending-bar" role="status">
            <GitPullRequestDraft className="ic" />
            <span><b>{pend.count} unpublished change{pend.count === 1 ? "" : "s"}</b> by {pend.contributors.join(", ")}. Agents still see version {t.version}.</span>
            <span className="spacer" />
            <button className="btn" onClick={() => setReviewing(true)}><GitPullRequestDraft className="ic" />{canEdit ? "Review & publish" : "Review changes"}</button>
          </div>
        )}
        {tab === "overview" && (
          <section className="card">
            <h3>What is this table?</h3>
            <p className="hint">Start with the grain and a description — that is what an agent reads first to decide whether this table answers a question.</p>
            <div className="fields">
              {biT("Grain — one row per …", "grain")}
              {biT("Description", "description", true)}
              {biT("Display name", "display_name")}
              <div className="three-col">
                <Select label="Table type" staged={stagedT("table_type")} value={t.table_type ?? ""} options={TABLE_TYPES} onSave={(v) => p({ table_type: v || null })} />
                <Text label="Domain" staged={stagedT("domain")} value={t.domain ?? ""} onSave={(v) => p({ domain: v || null })} />
                <Text label="Owner" staged={stagedT("owner")} value={t.owner ?? ""} onSave={(v) => p({ owner: v || null })} />
              </div>
            </div>
            <details className="more">
              <summary>More details — usage notes, caveats, PII, refresh</summary>
              <div className="fields" style={{ marginTop: 12 }}>
                {biT("Usage notes — how to query it well", "usage_notes", true)}
                {biT("Caveats — known gotchas", "caveats", true)}
                <div className="three-col">
                  <Select label="PII level" staged={stagedT("pii_level")} value={t.pii_level ?? ""} options={["", "none", "low", "high"]} onSave={(v) => p({ pii_level: v || null })} />
                  <Text label="Refresh cadence" staged={stagedT("refresh_cadence")} value={t.refresh_cadence ?? ""} onSave={(v) => p({ refresh_cadence: v || null })} />
                  <label className="check-inline" style={{ alignSelf: "end", paddingBottom: 8 }}><input type="checkbox" checked={t.certified} onChange={(e) => p({ certified: e.target.checked })} /> Certified source of truth</label>
                </div>
              </div>
            </details>
          </section>
        )}

        {tab === "columns" && (
          <section className="card">
            {t.quarantined_count > 0 && (
              <div className="qbanner">
                <EyeOff className="ic" /><span><b>{t.quarantined_count} column{t.quarantined_count === 1 ? " is" : "s are"} hidden from agents</b> until reviewed — new in the lake, or the name looks like personal data.</span>
                <span className="spacer" />
                <button className="btn" onClick={() => setOnly("hidden")}>Show them</button>
                {canEdit && <button className="btn" disabled={releaseAll.isPending} onClick={() => releaseAll.mutate(false)}><Eye className="ic" />Release all</button>}
              </div>
            )}
            <p className="hint" style={{ margin: "0 0 10px" }}>Click a column to edit it, or reuse one definition for every table that has the same column.</p>
            <div className="filterbar">
              <SearchInput value={cq} onChange={setCq} placeholder="Find a column…" label="Find a column" width={240} />
              <select aria-label="Filter columns" value={only} onChange={(e) => setOnly(e.target.value as any)} className="btn" style={{ padding: "6px 8px" }}>
                <option value="">All columns</option><option value="undocumented">No English description</option><option value="no_arabic">No Arabic description</option><option value="review">Needs review</option><option value="hidden">Hidden from agents</option>
              </select>
              <span className="muted">{cols.length === t.columns.length ? `${cols.length} columns` : `${cols.length} of ${t.columns.length}`}</span>
              <span style={{ flex: 1 }} />
              <button className="btn ghost" onClick={() => setOpen(open.size ? new Set() : new Set(cols.slice(0, 25).map((c) => c.id)))}>{open.size ? <><ChevronsDownUp className="ic" />Collapse all</> : <><ChevronsUpDown className="ic" />Expand first 25</>}</button>
            </div>
            {cols.map((c) => <ColumnRow key={c.id} c={c} tableId={id} open={open.has(c.id)} onToggle={() => toggle(c.id)} />)}
            {!cols.length && <EmptyState icon={SearchX} title="No columns match">Change the search or the filter above.</EmptyState>}
          </section>
        )}

        {tab === "history" && <section className="card"><h3><HistoryIcon className="ic" />Version history</h3><p className="hint">Each time changes to a published table go live, a new version is recorded. Restoring a version is staged for review like any other edit.</p><HistoryPanel tableId={id} /></section>}

        {tab === "preview" && (
          <section className="card">
            <h3>What agents see</h3>
            <p className="hint">{t.status === "published" ? `The live context served for this table${pend ? " — your unpublished changes are not included" : ""} (${previewLang === "both" ? "English + Arabic" : previewLang === "ar" ? "Arabic, English fallback" : "English"}). Change language with the toggle at the top.` : "This table is not published, so agents cannot see it yet."}</p>
            {canEdit && t.status !== "published" && <button className="btn primary" onClick={() => p({ status: "published", needs_review: false })}><Send className="ic" />Publish to agents</button>}
            {preview.isLoading && <div className="loading">Loading…</div>}
            {preview.data && <pre className="agent">{preview.data}</pre>}
          </section>
        )}

        {tab === "tech" && (
          <section className="card">
            <h3>Technical details</h3>
            <p className="hint">Read from the lake on each sync; not editable here.</p>
            <dl className="kv">
              <dt>Full name</dt><dd>{t.full_name}</dd>
              <dt>Format</dt><dd>{t.table_format ?? "—"}</dd>
              <dt>Location</dt><dd>{t.location ?? "—"}</dd>
              <dt>Partitioned by</dt><dd>{(t.partitioned_by ?? []).join(", ") || "—"}</dd>
              <dt>Rows</dt><dd>{t.row_count?.toLocaleString() ?? "—"}</dd>
            </dl>
          </section>
        )}
      </div>
      {reviewing && <PublishDialog tableId={id} name={t.full_name} onClose={() => setReviewing(false)} />}
    </div>
  );
}
