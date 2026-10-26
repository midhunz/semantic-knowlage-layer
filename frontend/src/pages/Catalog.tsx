import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { api, send } from "../api";
import { ArrowDown, ArrowUp, CheckCheck, Download, EyeOff, GitPullRequestDraft, FileSpreadsheet, Send, SearchX, Table2, Upload, Wand2, X } from "lucide-react";
import { useAuth } from "../auth";
import { Bi, Cov, EmptyState, Menu, Pager, SearchInput, SkeletonRows, StatusChip, useDebounced, useTitle, useToast, InfoTip } from "../ui";
import { HELP } from "../help";

const FILTER_KEYS = ["source_id", "schema", "status", "type", "domain", "owner", "needs_review", "missing", "q", "pending", "quarantined"];
const TYPES = ["", "fact", "dimension", "bridge", "staging", "aggregate"];
const PAGE_SIZE = 50;

const QUICK: { label: string; key: string; params: Record<string, string> }[] = [
  { label: "All", key: "all", params: {} },
  { label: "Needs review", key: "needs_review", params: { needs_review: "true" } },
  { label: "Pending changes", key: "pending", params: { pending: "true" } },
  { label: "Hidden columns", key: "quarantined", params: { quarantined: "true" } },
  { label: "No description", key: "description", params: { missing: "description" } },
  { label: "No grain", key: "grain", params: { missing: "grain" } },
  { label: "No Arabic", key: "arabic", params: { missing: "arabic" } },
  { label: "Columns undocumented", key: "columns", params: { missing: "columns" } },
  { label: "Unpublished", key: "draft", params: { status: "draft" } },
  { label: "Published", key: "published", params: { status: "published" } },
];

function SchemaCard({ schemaId }: { schemaId: number }) {
  const qc = useQueryClient();
  const toast = useToast();
  const { data: s } = useQuery({ queryKey: ["schema", schemaId], queryFn: () => api<any>(`/api/catalog/schemas/${schemaId}`) });
  const save = useMutation({
    mutationFn: (patch: object) => send("PATCH", `/api/catalog/schemas/${schemaId}`, patch),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["schema", schemaId] }); toast("Schema saved"); },
  });
  if (!s) return null;
  const p = (k: string) => (v: string) => save.mutate({ [k]: v || null });
  return (
    <details className="card" style={{ marginBottom: 12 }}>
      <summary style={{ cursor: "pointer", fontWeight: 650, color: "var(--petrol)" }}>
        About this schema — what lives in <code>{s.name}</code>?
        {!s.description && !s.description_ar && <span className="chip review" style={{ marginInlineStart: 8 }}>not described</span>}
      </summary>
      <p className="hint" style={{ marginTop: 8 }}>Agents get this as context for every table in the schema.</p>
      <div className="fields">
        <Bi label="Schema description" area en={s.description ?? ""} ar={s.description_ar ?? ""} onEn={p("description")} onAr={p("description_ar")} />
      </div>
    </details>
  );
}

export default function Catalog() {
  useTitle("Catalog");
  const qc = useQueryClient();
  const toast = useToast();
  const { canEdit } = useAuth();
  const [sp, setSp] = useSearchParams();
  const [qText, setQText] = useState(sp.get("q") ?? "");
  const debounced = useDebounced(qText);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [allMatching, setAllMatching] = useState(false);
  const [bulk, setBulk] = useState({ table_type: "", domain: "", owner: "" });
  const fileRef = useRef<HTMLInputElement>(null);
  const importKind = useRef<"columns" | "tables">("columns");

  const set = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(sp);
    Object.entries(patch).forEach(([k, v]) => (v ? next.set(k, v) : next.delete(k)));
    if (!("page" in patch)) next.delete("page");
    setSp(next, { replace: true });
  };
  useEffect(() => { if ((sp.get("q") ?? "") !== debounced) set({ q: debounced || null }); /* eslint-disable-next-line */ }, [debounced]);
  useEffect(() => { setQText(sp.get("q") ?? ""); /* eslint-disable-next-line */ }, [sp.get("q")]);

  const filters = useMemo(() => Object.fromEntries(FILTER_KEYS.filter((k) => sp.get(k)).map((k) => [k, sp.get(k)!])), [sp]);
  const query = new URLSearchParams(filters).toString();
  const sort = sp.get("sort") ?? "name";
  const order = sp.get("order") ?? "asc";
  const page = Number(sp.get("page") ?? 1);

  const list = useQuery({
    queryKey: ["catalog", query, sort, order, page],
    queryFn: () => api<any>(`/api/catalog/tables?${query}&sort=${sort}&order=${order}&page=${page}&page_size=${PAGE_SIZE}`),
    placeholderData: (prev) => prev,
  });
  const scope = new URLSearchParams(Object.fromEntries(["source_id", "schema"].filter((k) => filters[k]).map((k) => [k, filters[k]]))).toString();
  const counts = useQuery({ queryKey: ["stats", scope], queryFn: () => api<any>(`/api/catalog/stats?${scope}`) });
  const facets = useQuery({ queryKey: ["facets"], queryFn: () => api<any>("/api/catalog/facets") });
  const tree = useQuery({ queryKey: ["tree"], queryFn: () => api<any[]>("/api/catalog/tree") });
  const items: any[] = list.data?.items ?? [];
  const total: number = list.data?.total ?? 0;

  useEffect(() => { setSel(new Set()); setAllMatching(false); }, [query]);

  const schemaNode = tree.data?.find((s) => String(s.id) === filters.source_id)?.schemas.find((x: any) => x.name === filters.schema);
  const sourceName = tree.data?.find((s) => String(s.id) === filters.source_id)?.name;

  const refresh = () => {
    ["catalog", "stats", "tree", "facets", "table"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  };
  const bulkUpdate = useMutation({
    mutationFn: (patch: object) => send("POST", "/api/catalog/tables/bulk-update", allMatching ? { filters, patch } : { ids: [...sel], patch }),
    onSuccess: (r: any) => {
      const why = r.blocked ? ` · ${r.blocked} blocked by publishing rules (${r.blocked_examples[0]?.reason ?? ""})` : "";
      const st = r.staged ? ` · ${r.staged} saved as pending changes (published tables)` : "";
      toast(`Updated ${r.changed} of ${r.matched} tables${st}${why}`, !!r.blocked);
      refresh(); setBulk({ table_type: "", domain: "", owner: "" });
    },
    onError: (e) => toast(String(e), true),
  });
  const toggle = (id: number) => { const n = new Set(sel); n.has(id) ? n.delete(id) : n.add(id); setSel(n); setAllMatching(false); };
  const pageAll = items.length > 0 && items.every((r) => sel.has(r.id));
  const togglePage = () => { setSel(pageAll ? new Set() : new Set(items.map((r) => r.id))); setAllMatching(false); };
  const count = allMatching ? total : sel.size;

  const sortHeader = (key: string, label: string, num = false) => (
    <th className={`sortable${num ? " num" : ""}`} onClick={() => set({ sort: key, order: sort === key && order === "asc" ? "desc" : "asc" })}>
      {label}{sort === key && (order === "asc" ? <ArrowUp className="ic" /> : <ArrowDown className="ic" />)}
    </th>
  );

  const activeQuick = QUICK.findIndex((q) => {
    const keys = Object.keys(q.params);
    const others = FILTER_KEYS.filter((k) => !["q", "source_id", "schema"].includes(k) && sp.get(k));
    return keys.length === others.length && keys.every((k) => sp.get(k) === q.params[k]);
  });

  const doImport = async (file: File) => {
    const text = await file.text();
    const res = await fetch(`/api/catalog/import/${importKind.current}`, { method: "POST", body: text, headers: { "Content-Type": "text/csv" } });
    const r = await res.json();
    toast(res.ok ? `Imported: ${r.updated} of ${r.rows} rows updated${r.errors?.length ? ` · ${r.errors.length} problems (${r.errors[0]})` : ""}` : "Import failed", !res.ok || !!r.errors?.length);
    refresh();
  };

  return (
    <div className="page fill">
      <div className="page-head">
        <div>
          <div className="d-kind"><Table2 className="ic" />Catalog{sourceName ? ` · ${sourceName}` : ""}</div>
          <div className="d-title">{filters.schema ?? (sourceName ? "All schemas" : "All tables")} <InfoTip help={HELP.catalog} /></div>
        </div>
        <div className="head-spacer" />
        <Menu label={<><Download className="ic" />Export</>}>{(close) => (
          <>
            <a href={`/api/catalog/export/columns.csv?${query}`} onClick={close}>Columns CSV<small>Every column in the current view — edit in Excel</small></a>
            <a href={`/api/catalog/export/tables.csv?${query}`} onClick={close}>Tables CSV<small>Table-level fields for the current view</small></a>
          </>
        )}</Menu>
        {canEdit && <Menu label={<><Upload className="ic" />Import</>}>{(close) => (
          <>
            <button onClick={() => { importKind.current = "columns"; fileRef.current?.click(); close(); }}>Columns CSV…<small>Updates matching columns; blank cells are ignored</small></button>
            <button onClick={() => { importKind.current = "tables"; fileRef.current?.click(); close(); }}>Tables CSV…<small>Updates matching tables; blank cells are ignored</small></button>
          </>
        )}</Menu>}
        <input ref={fileRef} type="file" accept=".csv,text/csv" hidden onChange={(e) => { const f = e.target.files?.[0]; if (f) doImport(f); e.target.value = ""; }} />
      </div>

      {schemaNode?.schema_id && <SchemaCard schemaId={schemaNode.schema_id} />}

      <div className="pills">
        {QUICK.map((q, i) => (
          <button key={q.label} className={`pill${activeQuick === i ? " on" : ""}${counts.data?.worklists[q.key] === 0 && q.key !== "all" ? " zero" : ""}`}
            onClick={() => set({ needs_review: null, missing: null, status: null, pending: null, quarantined: null, ...q.params })}>
            {q.label}{counts.data && <span className="n">{counts.data.worklists[q.key].toLocaleString()}</span>}
          </button>
        ))}
      </div>

      <div className="toolbar">
        <SearchInput shortcut value={qText} onChange={setQText} placeholder="Search tables, columns, descriptions, synonyms (English or عربي)…" label="Search the catalog" />
        <select aria-label="Filter by type" value={filters.type ?? ""} onChange={(e) => set({ type: e.target.value || null })}>
          {TYPES.map((t) => <option key={t} value={t}>{t ? `Type: ${t}` : "Any type"}</option>)}
        </select>
        <select aria-label="Filter by domain" value={filters.domain ?? ""} onChange={(e) => set({ domain: e.target.value || null })}>
          <option value="">Any domain</option>
          {facets.data?.domains.map((d: any) => <option key={d.value} value={d.value}>{d.value} ({d.count})</option>)}
        </select>
        <select aria-label="Filter by owner" value={filters.owner ?? ""} onChange={(e) => set({ owner: e.target.value || null })}>
          <option value="">Any owner</option>
          {facets.data?.owners.map((d: any) => <option key={d.value} value={d.value}>{d.value} ({d.count})</option>)}
        </select>
        {Object.keys(filters).some((k) => !["source_id", "schema"].includes(k)) && (
          <button className="btn ghost" onClick={() => setSp(new URLSearchParams(Object.fromEntries(["source_id", "schema"].filter((k) => sp.get(k)).map((k) => [k, sp.get(k)!]))))}><X className="ic" />Clear filters</button>
        )}
      </div>

      <div className="grid-wrap">
        <table className="grid">
          <thead>
            <tr>
              <th style={{ width: 30 }}>{canEdit && <input type="checkbox" aria-label="Select all on this page" checked={pageAll} onChange={togglePage} />}</th>
              {sortHeader("name", "Table")}{sortHeader("type", "Type")}{sortHeader("domain", "Domain")}{sortHeader("owner", "Owner")}
              {sortHeader("status", "Status")}{sortHeader("columns", "Cols", true)}{sortHeader("en", "Documented")}
            </tr>
          </thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id} className={`${sel.has(r.id) || allMatching ? "sel" : ""}${r.removed ? " removed" : ""}`}>
                <td>{canEdit && <input type="checkbox" aria-label={`Select ${r.name}`} checked={sel.has(r.id) || allMatching} onChange={() => toggle(r.id)} />}</td>
                <td title={r.full_name} style={{ maxWidth: 420, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  <Link className="tname" to={`/tables/${r.id}`}><Table2 className="t-ic" />{r.display_name || r.name}</Link>
                  {r.display_name_ar && <span className="ar-text" dir="rtl" style={{ marginLeft: 8, color: "var(--ink-2)" }}>{r.display_name_ar}</span>}
                  <span className="sub" style={{ marginInlineStart: 8, fontFamily: "var(--mono)" }}>{r.source}.{r.schema}</span>
                  {r.needs_review && <span className="rv-dot" title="Needs review" />}
                  {r.pending && <span className="chip gold-soft with-ic" style={{ marginInlineStart: 8 }} title="Unpublished changes waiting for review"><GitPullRequestDraft className="ic" />pending</span>}
                  {r.quarantined > 0 && <span className="chip hold with-ic" style={{ marginInlineStart: 8 }} title="Columns hidden from agents until reviewed"><EyeOff className="ic" />{r.quarantined} hidden</span>}
                  {r.removed && <span className="chip warn" style={{ marginInlineStart: 8 }}>dropped</span>}
                </td>
                <td>{r.type ?? <span className="muted">—</span>}</td>
                <td>{r.domain ?? <span className="muted">—</span>}</td>
                <td>{r.owner ?? <span className="muted">—</span>}</td>
                <td><StatusChip status={r.status} /></td>
                <td className="num">{r.columns}</td>
                <td><Cov en={r.en} ar={r.ar} /></td>
              </tr>
            ))}
            {list.isLoading && <SkeletonRows rows={12} cols={8} />}
            {!items.length && !list.isLoading && (
              <tr><td colSpan={8}><EmptyState icon={SearchX} title="No tables match" actions={Object.keys(filters).length ? <button className="btn" onClick={() => setSp(new URLSearchParams())}>Clear all filters</button> : undefined}>
                {Object.keys(filters).length ? "Try removing a filter or searching for something else." : "Add a data lake source and sync it to see tables here."}
              </EmptyState></td></tr>
            )}
          </tbody>
        </table>
      </div>
      <Pager page={page} pageSize={PAGE_SIZE} total={total} onPage={(p) => set({ page: String(p) })} />

      {count > 0 && canEdit && (
        <div className="bulkbar">
          <b>{count.toLocaleString()} selected</b>
          {!allMatching && pageAll && total > items.length && <a onClick={() => setAllMatching(true)}>Select all {total.toLocaleString()} matching this filter</a>}
          {allMatching && <a onClick={() => { setAllMatching(false); setSel(new Set()); }}>Clear</a>}
          <span style={{ flex: 1 }} />
          <select aria-label="Set type for selected tables" value={bulk.table_type} onChange={(e) => setBulk({ ...bulk, table_type: e.target.value })}>
            {TYPES.map((t) => <option key={t} value={t}>{t ? `Type: ${t}` : "Set type…"}</option>)}
          </select>
          <input list="domains" placeholder="Set domain…" value={bulk.domain} onChange={(e) => setBulk({ ...bulk, domain: e.target.value })} />
          <input list="owners" placeholder="Set owner…" value={bulk.owner} onChange={(e) => setBulk({ ...bulk, owner: e.target.value })} />
          <datalist id="domains">{facets.data?.domains.map((d: any) => <option key={d.value} value={d.value} />)}</datalist>
          <datalist id="owners">{facets.data?.owners.map((d: any) => <option key={d.value} value={d.value} />)}</datalist>
          <button className="btn go" disabled={bulkUpdate.isPending || !(bulk.table_type || bulk.domain || bulk.owner)}
            onClick={() => bulkUpdate.mutate(Object.fromEntries(Object.entries(bulk).filter(([, v]) => v)))}>Apply</button>
          <button className="btn" onClick={() => bulkUpdate.mutate({ status: "reviewed", needs_review: false })}><CheckCheck className="ic" />Mark reviewed</button>
          <button className="btn go" onClick={() => bulkUpdate.mutate({ status: "published", needs_review: false })}><Send className="ic" />Publish</button>
          <button className="btn" onClick={() => bulkUpdate.mutate({ status: "draft" })}><EyeOff className="ic" />Unpublish</button>
        </div>
      )}
    </div>
  );
}
