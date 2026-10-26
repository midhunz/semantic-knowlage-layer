import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api";
import { Columns, FileText, Folder, History, SearchX, Table2 } from "lucide-react";
import { EmptyState, Pager, SearchInput, SkeletonRows, ago, useDebounced, when } from "../../ui";

const ENTITY_ICON: Record<string, any> = { table: Table2, column: Columns, schema: Folder };

const short = (v?: string | null) => (v == null || v === "" ? "∅" : v.length > 70 ? v.slice(0, 70) + "…" : v);

export default function Audit() {
  const [f, setF] = useState({ actor: "", entity: "", q: "" });
  const [page, setPage] = useState(1);
  const dq = useDebounced(f.q);
  const qs = new URLSearchParams({ page: String(page), page_size: "50", ...(f.actor && { actor: f.actor }), ...(f.entity && { entity: f.entity }), ...(dq && { q: dq }) });
  const { data } = useQuery({ queryKey: ["audit", qs.toString()], queryFn: () => api<any>(`/api/admin/audit?${qs}`), placeholderData: (p) => p });
  const set = (patch: Partial<typeof f>) => { setF({ ...f, ...patch }); setPage(1); };
  return (
    <section className="card">
      <h3><History className="ic" />Audit log</h3>
      <p className="hint">Every change to the catalog: who, what, and the old and new value.</p>
      <div className="toolbar">
        <SearchInput value={f.q} onChange={(v) => set({ q: v })} placeholder="Search field or value…" label="Search changes" />
        <select aria-label="Who" value={f.actor} onChange={(e) => set({ actor: e.target.value })}><option value="">Anyone</option>{data?.actors.map((a: string) => <option key={a} value={a}>{a}</option>)}</select>
        <select aria-label="What" value={f.entity} onChange={(e) => set({ entity: e.target.value })}><option value="">Everything</option><option value="table">Tables</option><option value="column">Columns</option><option value="schema">Schemas</option></select>
      </div>
      <div className="grid-wrap">
        <table className="grid">
          <thead><tr><th>When</th><th>Who</th><th>What</th><th>Field</th><th>Change</th></tr></thead>
          <tbody>
            {data?.items.map((r: any) => (
              <tr key={r.id}>
                <td title={when(r.at)} style={{ whiteSpace: "nowrap" }}>{ago(r.at)}</td>
                <td>{r.actor}</td>
                <td style={{ fontFamily: "var(--mono)", fontSize: 12 }}>{(() => { const I = ENTITY_ICON[r.entity] ?? FileText; return <I className="t-ic" />; })()}{r.target}</td>
                <td>{r.field.replace(/_/g, " ")}{r.staged && <span className="chip gold-soft" style={{ marginInlineStart: 6 }} title="Saved as a pending change">staged</span>}</td>
                <td dir="auto"><span className="muted">{short(r.old)}</span> → <b>{short(r.new)}</b></td>
              </tr>
            ))}
            {!data && <SkeletonRows rows={8} cols={5} />}
            {data && !data.items.length && <tr><td colSpan={5}><EmptyState icon={SearchX} title="No changes match" /></td></tr>}
          </tbody>
        </table>
      </div>
      {data && <Pager page={page} pageSize={50} total={data.total} onPage={setPage} />}
    </section>
  );
}
