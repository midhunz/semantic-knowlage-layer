import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api, send } from "../api";
import { ArrowDown, ArrowUp, Copy as CopyIcon, Eye, EyeOff, Gauge, Pencil, Plus, Trash2 } from "lucide-react";
import { useAuth } from "../auth";
import { Bi, CopyButton, EmptyState, Modal, Pager, SearchInput, Select, SkeletonRows, StatusChip, Tags, Text, ValueChips, useDebounced, useLang, useTitle, useToast, InfoTip } from "../ui";
import { HELP } from "../help";

const PAGE_SIZE = 25;
const STATUSES = ["draft", "reviewed", "published"];

type Form = {
  name: string; name_ar: string; description: string; description_ar: string; sql_expression: string; filters: string;
  synonyms: string[]; synonyms_ar: string[]; base_table_id: number | null; allowed_dimensions: string[]; owner: string; status: string;
};
const blank: Form = {
  name: "", name_ar: "", description: "", description_ar: "", sql_expression: "", filters: "", synonyms: [], synonyms_ar: [],
  base_table_id: null, allowed_dimensions: [], owner: "", status: "draft",
};

// The generic /api/metrics PUT replaces the whole row, so every field of a metric must be sent back —
// anything left out resets to the schema default (status -> "draft", allowed_dimensions -> []).
const toForm = (m: any): Form => ({
  name: m.name ?? "", name_ar: m.name_ar ?? "", description: m.description ?? "", description_ar: m.description_ar ?? "",
  sql_expression: m.sql_expression ?? "", filters: m.filters ?? "", synonyms: m.synonyms ?? [], synonyms_ar: m.synonyms_ar ?? [],
  base_table_id: m.base_table_id ?? null, allowed_dimensions: m.allowed_dimensions ?? [], owner: m.owner ?? "", status: m.status ?? "draft",
});
const toBody = (f: Form) => ({ ...f, filters: f.filters.trim() || null, name_ar: f.name_ar.trim() || null, description_ar: f.description_ar.trim() || null, owner: f.owner.trim() || null });

// search ignores Arabic diacritics and alef / ya / ta-marbuta variants, like the rest of the catalog
const norm = (s: string) => s.toLowerCase().replace(/[ً-ٰٟ]/g, "").replace(/[إأآ]/g, "ا").replace(/ى/g, "ي").replace(/ة/g, "ه");

const QUICK = [
  { key: "all", label: "All" },
  { key: "published", label: "Published" },
  { key: "draft", label: "Drafts" },
  { key: "reviewed", label: "Reviewed" },
  { key: "no_table", label: "No base table" },
  { key: "no_ar", label: "Missing Arabic" },
] as const;
type Quick = (typeof QUICK)[number]["key"];
type SortKey = "name" | "status" | "table";

export default function Metrics() {
  useTitle("Metrics");
  const qc = useQueryClient();
  const toast = useToast();
  const { canEdit } = useAuth();
  const [sp, setSp] = useSearchParams();
  const metrics = useQuery({ queryKey: ["metrics"], queryFn: () => api<any[]>("/api/metrics") });
  const tablesQ = useQuery({ queryKey: ["tables-for-metrics"], queryFn: () => api<any[]>("/api/tables") });
  const dimsQ = useQuery({ queryKey: ["dimensions-for-metrics"], queryFn: () => api<any[]>("/api/dimensions") });

  const tableFqnById = useMemo(() => new Map((tablesQ.data ?? []).map((t) => [t.id, t.fqn as string])), [tablesQ.data]);
  const dimKeys = useMemo(() => (dimsQ.data ?? []).map((d) => d.key as string), [dimsQ.data]);

  // ---- all view state lives in the URL, so any view (and any open metric) can be bookmarked or shared
  const quick = (sp.get("show") as Quick) || "all";
  const tableF = sp.get("table") || "";
  const ownerF = sp.get("owner") || "";
  const sortKey = (sp.get("sort") as SortKey) || "name";
  const desc = sp.get("dir") === "desc";
  const page = Math.max(1, Number(sp.get("page")) || 1);
  const openId = sp.get("open");
  const creating = sp.get("new") === "1";
  const fromId = sp.get("from");
  const set = (patch: Record<string, string | null>) => {
    const n = new URLSearchParams(sp);
    for (const [k, v] of Object.entries(patch)) (v ? n.set(k, v) : n.delete(k));
    if (!("page" in patch) && !("open" in patch) && !("new" in patch) && !("from" in patch)) n.delete("page");
    setSp(n, { replace: true });
  };
  const [qText, setQText] = useState(sp.get("q") ?? "");
  const dq = useDebounced(qText);
  useEffect(() => { if (dq !== (sp.get("q") ?? "")) set({ q: dq || null }); /* eslint-disable-next-line */ }, [dq]);

  const all = metrics.data ?? [];
  const hasAr = (m: any) => !!(m.name_ar && m.description_ar);
  const counts: Record<Quick, number> = useMemo(() => ({
    all: all.length,
    published: all.filter((m) => m.status === "published").length,
    draft: all.filter((m) => m.status === "draft").length,
    reviewed: all.filter((m) => m.status === "reviewed").length,
    no_table: all.filter((m) => !m.base_table_id).length,
    no_ar: all.filter((m) => !hasAr(m)).length,
  }), [all]);
  const tableOptions = useMemo(() => [...new Set(all.map((m) => m.base_table_id).filter(Boolean))].map((id) => ({ id: id as number, fqn: tableFqnById.get(id as number) ?? `table #${id}` })).sort((a, b) => a.fqn.localeCompare(b.fqn)), [all, tableFqnById]);
  const ownerOptions = useMemo(() => [...new Set(all.map((m) => m.owner).filter(Boolean))].sort() as string[], [all]);

  const rows = useMemo(() => {
    const needle = norm((sp.get("q") ?? "").trim());
    const out = all.filter((m) => {
      if (quick === "published" || quick === "draft" || quick === "reviewed") { if (m.status !== quick) return false; }
      if (quick === "no_table" && m.base_table_id) return false;
      if (quick === "no_ar" && hasAr(m)) return false;
      if (tableF && String(m.base_table_id) !== tableF) return false;
      if (ownerF && m.owner !== ownerF) return false;
      if (!needle) return true;
      return norm([m.name, m.name_ar, m.description, m.description_ar, m.sql_expression, m.filters, m.owner, tableFqnById.get(m.base_table_id), ...(m.synonyms ?? []), ...(m.synonyms_ar ?? []), ...(m.allowed_dimensions ?? [])].filter(Boolean).join(" ")).includes(needle);
    });
    const val = (m: any) => sortKey === "status" ? m.status : sortKey === "table" ? (tableFqnById.get(m.base_table_id) ?? "~") : (m.name ?? "").toLowerCase();
    out.sort((a, b) => { const x = val(a), y = val(b); const c = typeof x === "number" ? x - (y as number) : String(x).localeCompare(String(y)); return (desc ? -c : c) || a.name.localeCompare(b.name); });
    return out;
  }, [all, sp, quick, tableF, ownerF, sortKey, desc, tableFqnById]);

  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const cur = Math.min(page, pages);
  const shown = rows.slice((cur - 1) * PAGE_SIZE, cur * PAGE_SIZE);

  // ---- selection (bulk actions)
  const [sel, setSel] = useState<Set<number>>(new Set());
  const pageAll = shown.length > 0 && shown.every((m) => sel.has(m.id));
  const toggle = (id: number) => setSel((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const togglePage = () => setSel((s) => { const n = new Set(s); shown.forEach((m) => (pageAll ? n.delete(m.id) : n.add(m.id))); return n; });

  const refresh = () => qc.invalidateQueries({ queryKey: ["metrics"] });
  const del = useMutation({
    mutationFn: (ids: number[]) => Promise.all(ids.map((id) => send("DELETE", `/api/metrics/${id}`))),
    onSuccess: (_r, ids) => { refresh(); setSel(new Set()); toast(ids.length === 1 ? "Metric deleted" : `${ids.length} metrics deleted`); },
    onError: (e) => toast(String((e as Error).message ?? e), true),
  });
  const setStatus = useMutation({
    mutationFn: ({ ids, status }: { ids: number[]; status: string }) => Promise.all(ids.map((id) => send("PUT", `/api/metrics/${id}`, toBody({ ...toForm(all.find((m) => m.id === id)), status })))),
    onSuccess: (_r, v) => { refresh(); setSel(new Set()); toast(`${v.ids.length} ${v.ids.length === 1 ? "metric" : "metrics"} → ${v.status}`); },
    onError: (e) => toast(String((e as Error).message ?? e), true),
  });
  const confirmDelete = (ms: any[]) => {
    const what = ms.length === 1 ? `the metric “${ms[0].name}”` : `${ms.length} metrics`;
    if (window.confirm(`Delete ${what}? Agents stop seeing ${ms.length === 1 ? "it" : "them"} immediately. This cannot be undone.`)) del.mutate(ms.map((m) => m.id));
  };

  const sortBy = (k: SortKey) => set({ sort: k === "name" && !desc && sortKey === "name" ? null : k, dir: sortKey === k && !desc ? "desc" : null });
  const th = (k: SortKey, label: string, cls = "") => (
    <th className={`sortable ${cls}`} aria-sort={sortKey === k ? (desc ? "descending" : "ascending") : "none"}>
      <button type="button" className="th-btn" onClick={() => sortBy(k)}>{label}{sortKey === k && (desc ? <ArrowDown className="ic" /> : <ArrowUp className="ic" />)}</button>
    </th>
  );

  const openEditor = (id: number) => set({ open: String(id), new: null, from: null });
  const closeEditor = () => set({ open: null, new: null, from: null });
  const editing = openId ? all.find((m) => String(m.id) === openId) : null;
  const source = fromId ? all.find((m) => String(m.id) === fromId) : null;
  const filtered = quick !== "all" || tableF || ownerF || (sp.get("q") ?? "");
  const clearFilters = () => { setQText(""); set({ show: null, table: null, owner: null, q: null }); };

  return (
    <div className="page fill">
      <div className="page-head">
        <div><div className="d-kind"><Gauge className="ic" />Business definitions</div><div className="d-title">Metrics <InfoTip help={HELP.metrics} /></div></div>
        <div className="head-spacer" />
        {canEdit && <button className="btn primary" onClick={() => set({ new: "1", open: null, from: null })}><Plus className="ic" />New metric</button>}
      </div>

      <div className="pills">
        {QUICK.map((q) => (
          <button key={q.key} className={`pill${quick === q.key ? " on" : ""}${counts[q.key] === 0 && q.key !== "all" ? " zero" : ""}`} onClick={() => set({ show: q.key === "all" ? null : q.key })}>
            {q.label}<span className="n">{counts[q.key].toLocaleString()}</span>
          </button>
        ))}
      </div>

      <div className="toolbar">
        <SearchInput shortcut value={qText} onChange={setQText} placeholder="Search name, definition, SQL, synonyms (English or عربي)…" label="Search metrics" width={380} />
        <select aria-label="Filter by base table" value={tableF} onChange={(e) => set({ table: e.target.value || null })}>
          <option value="">Any base table</option>
          {tableOptions.map((t) => <option key={t.id} value={t.id}>{t.fqn}</option>)}
        </select>
        <select aria-label="Filter by owner" value={ownerF} onChange={(e) => set({ owner: e.target.value || null })}>
          <option value="">Any owner</option>
          {ownerOptions.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        {filtered && <button className="btn ghost" onClick={clearFilters}>Clear filters</button>}
        <span className="head-spacer" />
        <span className="muted" aria-live="polite">{rows.length.toLocaleString()} of {all.length.toLocaleString()} metrics</span>
      </div>

      <div className="grid-wrap">
        <table className="grid mt">
          <thead>
            <tr>
              <th style={{ width: 34 }}>{canEdit && <input type="checkbox" aria-label="Select all on this page" checked={pageAll} onChange={togglePage} />}</th>
              {th("name", "Metric")}
              <th>Calculation</th>
              {th("table", "Base table")}
              {th("status", "Status")}
              <th>Language</th>
              <th style={{ width: 120 }}><span className="sr-only">Actions</span></th>
            </tr>
          </thead>
          <tbody>
            {shown.map((m) => (
              <tr key={m.id} className={sel.has(m.id) ? "sel" : ""}>
                <td>{canEdit && <input type="checkbox" aria-label={`Select ${m.name}`} checked={sel.has(m.id)} onChange={() => toggle(m.id)} />}</td>
                <td className="mt-name">
                  <button type="button" className="tname linklike" onClick={() => openEditor(m.id)}><Gauge className="t-ic" />{m.name}</button>
                  {m.name_ar && <span className="ar-text" dir="rtl" lang="ar"> {m.name_ar}</span>}
                  <div className="sub mt-clip" title={m.description || ""}>{m.description || <i>No definition yet</i>}</div>
                </td>
                <td className="mt-sql"><code title={m.sql_expression + (m.filters ? `  WHERE ${m.filters}` : "")}>{m.sql_expression}</code>{m.filters && <div className="sub mt-clip" title={m.filters}>where {m.filters}</div>}</td>
                <td>{m.base_table_id ? <span className="mt-clip" title={tableFqnById.get(m.base_table_id)}>{tableFqnById.get(m.base_table_id) ?? `table #${m.base_table_id}`}</span> : <span className="chip warn">none</span>}</td>
                <td><StatusChip status={m.status} /></td>
                <td><span className="lang-cell"><span className={`lang-dot en${m.description ? " on" : ""}`} title={m.description ? "English definition written" : "English definition missing"} /><span className={`lang-dot ar${hasAr(m) ? " on" : ""}`} title={hasAr(m) ? "Arabic name and definition written" : "Arabic name or definition missing"} /><span className="sr-only">{m.description ? "EN ok" : "EN missing"}, {hasAr(m) ? "AR ok" : "AR missing"}</span></span></td>
                <td className="mt-actions">
                  <button className="btn" onClick={() => openEditor(m.id)}>{canEdit ? <><Pencil className="ic" />Edit</> : <><Eye className="ic" />View</>}</button>
                  {canEdit && <>
                    <button className="btn icon-only" title="Duplicate" aria-label={`Duplicate ${m.name}`} onClick={() => set({ new: "1", from: String(m.id), open: null })}><CopyIcon className="ic" /></button>
                    <button className="btn icon-only danger" title="Delete" aria-label={`Delete ${m.name}`} onClick={() => confirmDelete([m])}><Trash2 className="ic" /></button>
                  </>}
                </td>
              </tr>
            ))}
            {metrics.isLoading && <SkeletonRows rows={6} cols={7} />}
            {metrics.data && !rows.length && (
              <tr><td colSpan={7}>
                <EmptyState icon={Gauge} title={filtered ? "No metric matches" : "No metrics yet"}
                  actions={filtered ? <button className="btn" onClick={clearFilters}>Clear filters</button> : canEdit ? <button className="btn primary" onClick={() => set({ new: "1" })}><Plus className="ic" />New metric</button> : undefined}>
                  {filtered ? "Try another word or remove a filter." : "Define governed numbers like “net revenue” once, so agents use them verbatim."}
                </EmptyState>
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
      {rows.length > PAGE_SIZE && <Pager page={cur} pageSize={PAGE_SIZE} total={rows.length} onPage={(p) => set({ page: p > 1 ? String(p) : null })} />}

      {canEdit && sel.size > 0 && (
        <div className="bulkbar">
          <b>{sel.size.toLocaleString()} selected</b>
          <button className="linklike-w" onClick={() => setSel(new Set())}>Clear</button>
          <span style={{ flex: 1 }} />
          <button className="btn" disabled={setStatus.isPending} onClick={() => setStatus.mutate({ ids: [...sel], status: "published" })}><Eye className="ic" />Publish</button>
          <button className="btn" disabled={setStatus.isPending} onClick={() => setStatus.mutate({ ids: [...sel], status: "draft" })}><EyeOff className="ic" />Move to draft</button>
          <button className="btn" disabled={del.isPending} onClick={() => confirmDelete(all.filter((m) => sel.has(m.id)))}><Trash2 className="ic" />Delete</button>
        </div>
      )}

      {(editing || creating) && (
        <MetricEditor key={editing?.id ?? `new-${fromId ?? ""}`} metric={editing ?? null} source={source ?? null} all={all} tableFqnById={tableFqnById}
          tables={tablesQ.data ?? []} dimKeys={dimKeys} canEdit={canEdit} onClose={closeEditor}
          onSaved={(msg) => { refresh(); toast(msg); closeEditor(); }} />
      )}
      {openId && metrics.data && !editing && <MissingMetric onClose={closeEditor} />}
    </div>
  );
}

function MissingMetric({ onClose }: { onClose: () => void }) {
  useEffect(() => { onClose(); /* eslint-disable-next-line */ }, []);
  return null;
}

/* ------------------------------------------------------------------ editor */
function MetricEditor({ metric, source, all, tables, tableFqnById, dimKeys, canEdit, onClose, onSaved }: {
  metric: any | null; source: any | null; all: any[]; tables: any[]; tableFqnById: Map<number, string>; dimKeys: string[]; canEdit: boolean;
  onClose: () => void; onSaved: (msg: string) => void;
}) {
  const initial: Form = metric ? toForm(metric) : source ? { ...toForm(source), name: `${source.name} (copy)`, name_ar: source.name_ar ? `${source.name_ar} (نسخة)` : "", status: "draft" } : blank;
  const [f, setF] = useState<Form>(initial);
  const first = useRef(JSON.stringify(initial));
  const dirty = JSON.stringify(f) !== first.current;
  const up = (patch: Partial<Form>) => setF((x) => ({ ...x, ...patch }));
  const { lang } = useLang();

  const tableIdByFqn = new Map(tables.map((t) => [t.fqn as string, t.id as number]));
  const dupe = all.some((m) => m.id !== metric?.id && m.name.trim().toLowerCase() === f.name.trim().toLowerCase());
  const problem = !f.name.trim() ? "Add a name" : dupe ? "Another metric already uses this name" : !f.sql_expression.trim() ? "Add the SQL expression" : "";
  const dimOptions = [...new Set([...dimKeys, ...f.allowed_dimensions])];
  const unknownDims = f.allowed_dimensions.filter((d) => !dimKeys.includes(d));
  const tableFqn = f.base_table_id ? tableFqnById.get(f.base_table_id) ?? `table #${f.base_table_id}` : "";
  const preview = `SELECT ${f.sql_expression.trim() || "<expression>"}\nFROM ${tableFqn || "<base table>"}${f.filters.trim() ? `\nWHERE ${f.filters.trim()}` : ""}`;

  const close = () => { if (!dirty || window.confirm("Discard your unsaved changes to this metric?")) onClose(); };
  const save = useMutation({
    mutationFn: (status: string) => { const body = toBody({ ...f, status }); return metric ? send("PUT", `/api/metrics/${metric.id}`, body) : send("POST", "/api/metrics", body); },
    onSuccess: (_r, status) => onSaved(metric ? `Saved “${f.name}”` : status === "published" ? `Published “${f.name}”` : `Created “${f.name}” as ${status}`),
  });

  // Ctrl/Cmd+Enter saves
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter" && canEdit && !problem && !save.isPending) save.mutate(f.status); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  const footer = (
    <>
      {canEdit && dirty && !problem && <span className="muted" style={{ marginInlineEnd: "auto" }}>Unsaved changes · Ctrl+Enter to save</span>}
      {canEdit && problem && <span className="mt-problem" style={{ marginInlineEnd: "auto" }} role="status">Can’t save yet — {problem.charAt(0).toLowerCase() + problem.slice(1)}</span>}
      <button className="btn" onClick={close}>{canEdit ? "Cancel" : "Close"}</button>
      {canEdit && (metric
        ? <button className="btn primary" disabled={!!problem || !dirty || save.isPending} onClick={() => save.mutate(f.status)}>{save.isPending ? "Saving…" : "Save changes"}</button>
        : <>
            <button className="btn" disabled={!!problem || save.isPending} onClick={() => save.mutate("draft")}>Save as draft</button>
            <button className="btn primary" disabled={!!problem || save.isPending} onClick={() => save.mutate("published")}>Save & publish</button>
          </>)}
    </>
  );

  return (
    <Modal width={900} title={metric ? (canEdit ? "Edit metric" : "Metric") : source ? "Duplicate metric" : "New metric"}
      sub={metric ? metric.name : source ? `Copy of ${source.name} — saved as a draft until you publish` : "Saved as a draft unless you publish it"} onClose={close} footer={footer}>
      <div className="mt-form">
        <section>
          <h4>What it means</h4>
          <Bi label="Name" en={f.name} ar={f.name_ar} onEn={(v) => up({ name: v })} onAr={(v) => up({ name_ar: v })} />
          {dupe && <div className="mt-problem">Another metric already uses this name.</div>}
          <Bi label="Definition — what it counts and when to use it" area en={f.description} ar={f.description_ar} onEn={(v) => up({ description: v })} onAr={(v) => up({ description_ar: v })} />
        </section>

        <section>
          <h4>How it is calculated</h4>
          <div className="two-col">
            <div className="field">
              <label htmlFor="mt-sql">SQL expression</label>
              <textarea id="mt-sql" className="mono" rows={2} spellCheck={false} dir="ltr" readOnly={!canEdit} placeholder="e.g. SUM(net_amount)" value={f.sql_expression} onChange={(e) => up({ sql_expression: e.target.value })} />
            </div>
            <div className="field">
              <label htmlFor="mt-filters">Filter (optional)</label>
              <textarea id="mt-filters" className="mono" rows={2} spellCheck={false} dir="ltr" readOnly={!canEdit} placeholder="e.g. status = 'ACTIVE'" value={f.filters} onChange={(e) => up({ filters: e.target.value })} />
            </div>
          </div>
          <Select label="Base table" value={tableFqn} options={["", ...tables.map((t) => t.fqn)]} onSave={(v) => up({ base_table_id: v ? tableIdByFqn.get(v) ?? null : null })} />
          <div className="mt-preview">
            <div className="mt-preview-head"><span>The query agents will build from this</span><CopyButton text={preview} /></div>
            <pre>{preview}</pre>
          </div>
        </section>

        <section>
          <h4>How people ask for it</h4>
          {lang !== "ar" && <div className="field"><label>Synonyms · English <span className="hint-inline">type a word, press Enter</span></label><Tags label="English synonyms" value={f.synonyms} onChange={(v) => up({ synonyms: v })} disabled={!canEdit} placeholder="e.g. revenue, sales, turnover" /></div>}
          {lang !== "en" && <div className="field ar"><label>مرادفات · عربي</label><Tags label="Arabic synonyms" value={f.synonyms_ar} onChange={(v) => up({ synonyms_ar: v })} disabled={!canEdit} placeholder="أضف كلمة ثم Enter" /></div>}
          <div className="field">
            <label>Dimensions it can be broken down by <span className="hint-inline">{f.allowed_dimensions.length} chosen · click to toggle</span></label>
            <ValueChips options={dimOptions} value={f.allowed_dimensions} onChange={(v) => up({ allowed_dimensions: v })} disabled={!canEdit} />
            {unknownDims.length > 0 && <div className="mt-problem">Not a known dimension: {unknownDims.join(", ")}. Deselect to remove.</div>}
          </div>
        </section>

        <section>
          <h4>Ownership</h4>
          <div className="two-col">
            <Text label="Owner" value={f.owner} onSave={(v) => up({ owner: v })} placeholder="Person or team accountable for this number" />
            <Select label="Status" value={f.status} options={STATUSES} onSave={(v) => up({ status: v })} />
          </div>
          <div className="hint">Only <b>published</b> metrics are visible to agents. Drafts and reviewed metrics stay private.</div>
        </section>
        {save.error && <div className="banner bad" role="alert">{String((save.error as Error).message ?? save.error)}</div>}
      </div>
    </Modal>
  );
}
