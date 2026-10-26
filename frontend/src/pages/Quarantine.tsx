import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router-dom";
import { Eye, EyeOff, ShieldAlert, ShieldCheck, Sparkles } from "lucide-react";
import { api, errText, send } from "../api";
import { useAuth } from "../auth";
import { EmptyState, Pager, SearchInput, SkeletonRows, useDebounced, useTitle, useToast, InfoTip } from "../ui";
import { HELP } from "../help";

const PAGE = 50;

export default function Quarantine() {
  useTitle("Quarantine");
  const qc = useQueryClient();
  const toast = useToast();
  const { canEdit } = useAuth();
  const [sp, setSp] = useSearchParams();
  const [q, setQ] = useState("");
  const dq = useDebounced(q);
  const [page, setPage] = useState(1);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [all, setAll] = useState(false);
  const reason = sp.get("reason") ?? "";
  const scope = new URLSearchParams(Object.fromEntries(["source_id", "schema"].filter((k) => sp.get(k)).map((k) => [k, sp.get(k)!])));

  const qs = new URLSearchParams({ page: String(page), page_size: String(PAGE), ...(reason && { reason }), ...(dq && { q: dq }), ...Object.fromEntries(scope) });
  const { data, isLoading } = useQuery({ queryKey: ["quarantine", qs.toString()], queryFn: () => api<any>(`/api/catalog/quarantine?${qs}`), placeholderData: (p) => p });
  const items: any[] = data?.items ?? [];
  useEffect(() => { setSel(new Set()); setAll(false); }, [reason, dq, page]);

  const filters = { ...(reason && { reason }), ...Object.fromEntries(scope) };
  const refresh = () => ["quarantine", "stats", "catalog", "table", "tree"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  const release = useMutation({
    mutationFn: (mark_pii: boolean) => send("POST", "/api/catalog/quarantine/release", all ? { filters, mark_pii } : { ids: [...sel], mark_pii }),
    onSuccess: (r: any) => { refresh(); setSel(new Set()); setAll(false); toast(`Released ${r.released} column${r.released === 1 ? "" : "s"}${r.marked_pii ? " as personal data" : ""}`); },
    onError: (e) => toast(errText(e), true),
  });
  const one = useMutation({
    mutationFn: ({ id, mark_pii }: { id: number; mark_pii: boolean }) => send("POST", "/api/catalog/quarantine/release", { ids: [id], mark_pii }),
    onSuccess: () => { refresh(); toast("Released"); },
    onError: (e) => toast(errText(e), true),
  });

  const pageAll = items.length > 0 && items.every((r) => sel.has(r.id));
  const count = all ? data?.total ?? 0 : sel.size;
  const toggle = (id: number) => { const n = new Set(sel); n.has(id) ? n.delete(id) : n.add(id); setSel(n); setAll(false); };

  return (
    <div className="page fill">
      <div className="page-head">
        <div><div className="d-kind"><ShieldAlert className="ic" />Review before agents see it</div><div className="d-title">Quarantine <InfoTip help={HELP.quarantine} /></div></div>
      </div>
      <div className="toolbar">
        <SearchInput shortcut value={q} onChange={(v) => { setQ(v); setPage(1); }} placeholder="Find a column or table…" label="Find a quarantined column" />
        <select aria-label="Why it is held" value={reason} onChange={(e) => { const n = new URLSearchParams(sp); e.target.value ? n.set("reason", e.target.value) : n.delete("reason"); setSp(n, { replace: true }); setPage(1); }}>
          <option value="">Any reason</option><option value="new">New column</option><option value="sensitive">Sensitive-looking name</option>
        </select>
        <span className="muted">{data ? `${data.total.toLocaleString()} waiting` : ""}</span>
      </div>

      <div className="grid-wrap">
        <table className="grid">
          <thead><tr>
            <th style={{ width: 30 }}>{canEdit && <input type="checkbox" aria-label="Select all on this page" checked={pageAll} onChange={() => { setSel(pageAll ? new Set() : new Set(items.map((r) => r.id))); setAll(false); }} />}</th>
            <th>Column</th><th>Table</th><th>Type</th><th>Why it is held</th><th style={{ textAlign: "right" }}>Release</th>
          </tr></thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.id} className={sel.has(r.id) || all ? "sel" : ""}>
                <td>{canEdit && <input type="checkbox" aria-label={`Select ${r.column}`} checked={sel.has(r.id) || all} onChange={() => toggle(r.id)} />}</td>
                <td><b style={{ fontFamily: "var(--mono)", color: "var(--petrol)" }}>{r.column}</b></td>
                <td><Link className="tname" to={`/tables/${r.table_id}?tab=columns`}>{r.table}</Link>{r.published && <span className="chip ok" style={{ marginInlineStart: 8 }}>published</span>}</td>
                <td className="sub">{r.data_type}</td>
                <td>{r.reason}</td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  {canEdit && <>
                    <button className="btn" disabled={one.isPending} onClick={() => one.mutate({ id: r.id, mark_pii: false })}><Eye className="ic" />Release</button>{" "}
                    <button className="btn" disabled={one.isPending} onClick={() => one.mutate({ id: r.id, mark_pii: true })} title="Release it, but flag it as personal data"><ShieldCheck className="ic" />As personal data</button>
                  </>}
                </td>
              </tr>
            ))}
            {isLoading && <SkeletonRows rows={8} cols={6} />}
            {data && !items.length && <tr><td colSpan={6}><EmptyState icon={Sparkles} title="Nothing waiting for review">New columns and sensitive-looking names will appear here after the next sync.</EmptyState></td></tr>}
          </tbody>
        </table>
      </div>
      {data && <Pager page={page} pageSize={PAGE} total={data.total} onPage={setPage} />}

      {count > 0 && canEdit && (
        <div className="bulkbar">
          <b>{count.toLocaleString()} selected</b>
          {!all && pageAll && data.total > items.length && <a onClick={() => setAll(true)}>Select all {data.total.toLocaleString()} matching this filter</a>}
          {all && <a onClick={() => { setAll(false); setSel(new Set()); }}>Clear</a>}
          <span style={{ flex: 1 }} />
          <button className="btn go" disabled={release.isPending} onClick={() => release.mutate(false)}><Eye className="ic" />Release to agents</button>
          <button className="btn" disabled={release.isPending} onClick={() => release.mutate(true)}><ShieldCheck className="ic" />Release as personal data</button>
        </div>
      )}
    </div>
  );
}
