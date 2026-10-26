import { Fragment, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, send } from "../api";
import { BookOpen, ChevronDown, ChevronRight, Layers, PartyPopper, Search, Sparkles } from "lucide-react";
import { useAuth } from "../auth";
import { Bi, EmptyState, Pager, SearchInput, Select, SkeletonRows, Text, csv, useDebounced, useTitle, useToast, InfoTip } from "../ui";
import { HELP } from "../help";

const ROLES = ["", "identifier", "dimension", "measure", "time", "attribute"];
const AGGS = ["", "sum", "avg", "min", "max", "count", "none"];
const PAGE_SIZE = 40;

function Progress({ done, total, ar }: { done: number; total: number; ar?: boolean }) {
  const f = total ? done / total : 0;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 8, alignItems: "center" }}>
      <div className={`meter${ar ? " ar" : ""}`} style={{ margin: 0, maxWidth: "none" }}><i style={{ width: `${Math.round(f * 100)}%` }} /></div>
      <span className="sub" style={{ fontVariantNumeric: "tabular-nums" }}>{done}/{total}</span>
    </div>
  );
}

function Editor({ g, onDone }: { g: any; onDone: () => void }) {
  const { canEdit } = useAuth();
  const qc = useQueryClient();
  const toast = useToast();
  // start from the best documented instance of this column name
  const base = { ...Object.fromEntries(Object.entries(g.definition).filter(([, v]) => v && !(Array.isArray(v) && !v.length) && !(typeof v === "object" && !Array.isArray(v) && !Object.keys(v as object).length))) } as any;
  const [d, setD] = useState<any>(base);
  const up = (k: string) => (v: any) => setD((x: any) => ({ ...x, [k]: v }));
  const apply = useMutation({
    mutationFn: (only_empty: boolean) => send("POST", "/api/catalog/column-groups/apply", { name: g.name, only_empty, patch: Object.fromEntries(Object.entries(d).filter(([, v]) => v !== "" && v != null)) }),
    onSuccess: (r: any) => { toast(`${r.updated} of ${r.matched} columns updated across ${r.tables} tables`); ["colgroups", "stats", "tables", "catalog", "table"].forEach((k) => qc.invalidateQueries({ queryKey: [k] })); onDone(); },
    onError: (e) => toast(String(e), true),
  });
  const blanks = g.occurrences - Math.min(g.documented, g.occurrences);
  return (
    <div>
      <p className="hint">One definition for every column named <code>{g.name}</code> ({g.occurrences} columns in {g.tables} tables{g.mixed_types ? ", mixed data types — check before overwriting" : ""}).</p>
      <div className="fields">
        <Bi label="Display name" en={d.display_name ?? ""} ar={d.display_name_ar ?? ""} onEn={up("display_name")} onAr={up("display_name_ar")} />
        <Bi label="Description" area en={d.description ?? ""} ar={d.description_ar ?? ""} onEn={up("description")} onAr={up("description_ar")} />
        <div className="three-col">
          <Select label="Role" value={d.role ?? ""} options={ROLES} onSave={up("role")} />
          <Select label="Default aggregation" value={d.default_aggregation ?? ""} options={AGGS} onSave={up("default_aggregation")} />
          <Text label="Semantic type" value={d.semantic_type ?? ""} onSave={up("semantic_type")} />
        </div>
        <div className="two-col">
          <Text label="Synonyms · EN (comma separated)" value={(d.synonyms ?? []).join(", ")} onSave={(v) => up("synonyms")(csv(v))} />
          <Text rtl label="مرادفات · عربي (مفصولة بفاصلة)" value={(d.synonyms_ar ?? []).join("، ")} onSave={(v) => up("synonyms_ar")(csv(v))} />
        </div>
      </div>
      {canEdit && <div className="apply-all">
        <button className="btn primary" disabled={apply.isPending} onClick={() => apply.mutate(true)}>Apply to {blanks.toLocaleString()} empty columns</button>
        <button className="btn danger" disabled={apply.isPending}
          onClick={() => window.confirm(`Overwrite these fields on all ${g.occurrences} columns named ${g.name}? Existing text in them will be replaced.`) && apply.mutate(false)}>Overwrite all {g.occurrences.toLocaleString()}</button>
        <span className="muted">Only the fields filled in above are applied; blank fields are left alone.</span>
      </div>}
    </div>
  );
}

export default function ColumnDictionary() {
  useTitle("Column dictionary");
  const [q, setQ] = useState("");
  const dq = useDebounced(q);
  const [missing, setMissing] = useState("description");
  const [sort, setSort] = useState("undocumented");
  const [page, setPage] = useState(1);
  const [open, setOpen] = useState<string | null>(null);
  const { data } = useQuery({
    queryKey: ["colgroups", dq, missing, sort, page],
    queryFn: () => api<any>(`/api/catalog/column-groups?q=${encodeURIComponent(dq)}&missing=${missing}&sort=${sort}&page=${page}&page_size=${PAGE_SIZE}`),
    placeholderData: (prev) => prev,
  });
  return (
    <div className="page fill">
      <div className="page-head"><div><div className="d-kind"><BookOpen className="ic" />Document once, apply everywhere</div><div className="d-title">Column dictionary <InfoTip help={HELP.columns} /></div></div></div>
      <div className="toolbar">
        <SearchInput shortcut value={q} onChange={(v) => { setQ(v); setPage(1); }} placeholder="Find a column name…" label="Find a column name" />
        <select aria-label="Show columns" value={missing} onChange={(e) => { setMissing(e.target.value); setPage(1); }}>
          <option value="description">Missing English description</option><option value="arabic">Missing Arabic description</option><option value="">All columns</option>
        </select>
        <select aria-label="Sort order" value={sort} onChange={(e) => setSort(e.target.value)}>
          <option value="undocumented">Most undocumented first</option><option value="occurrences">Most common first</option><option value="name">A → Z</option>
        </select>
      </div>
      <div className="grid-wrap">
        <table className="grid">
          <thead><tr><th>Column name</th><th>Type</th><th className="num">In tables</th><th style={{ width: 170 }}>English</th><th style={{ width: 170 }}>Arabic</th><th /></tr></thead>
          <tbody>
            {data?.items.map((g: any) => (
              <Fragment key={g.name}>
                <tr className="clickable" onClick={() => setOpen(open === g.name ? null : g.name)}>
                  <td><b style={{ fontFamily: "var(--mono)", color: "var(--petrol)" }}>{g.name}</b>{g.mixed_types && <span className="chip warn" style={{ marginInlineStart: 8 }} title="This name has different data types in different tables">mixed types</span>}</td>
                  <td className="sub">{g.data_type}</td>
                  <td className="num">{g.tables.toLocaleString()}</td>
                  <td><Progress done={g.documented} total={g.occurrences} /></td>
                  <td><Progress done={g.documented_ar} total={g.occurrences} ar /></td>
                  <td className="def-btn">{open === g.name ? <>Close<ChevronDown className="ic" /></> : <>Define<ChevronRight className="ic" /></>}</td>
                </tr>
                {open === g.name && <tr className="expand"><td colSpan={6}><Editor g={g} onDone={() => setOpen(null)} /></td></tr>}
              </Fragment>
            ))}
            {!data && <SkeletonRows rows={10} cols={6} />}
            {data && !data.items.length && <tr><td colSpan={6}><EmptyState icon={Sparkles} title="Nothing left to document here">Every column matching this view already has a description.</EmptyState></td></tr>}
          </tbody>
        </table>
      </div>
      {data && <Pager page={page} pageSize={PAGE_SIZE} total={data.total} onPage={setPage} />}
    </div>
  );
}
