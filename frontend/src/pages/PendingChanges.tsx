import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { GitPullRequestDraft, Send, Sparkles, Undo2 } from "lucide-react";
import { api, errText, send } from "../api";
import { useAuth } from "../auth";
import { PublishDialog } from "../revisions";
import { EmptyState, Modal, Pager, SearchInput, SkeletonRows, ago, useDebounced, useTitle, useToast, InfoTip } from "../ui";
import { HELP } from "../help";
import { ReviewQueue } from "../review";

const PAGE = 50;

export default function PendingChanges() {
  useTitle("Pending changes");
  const qc = useQueryClient();
  const toast = useToast();
  const { canEdit } = useAuth();
  const [q, setQ] = useState("");
  const dq = useDebounced(q);
  const [page, setPage] = useState(1);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const [reviewing, setReviewing] = useState<{ id: number; name: string } | null>(null);
  const [confirm, setConfirm] = useState<"publish" | "discard" | null>(null);
  const [message, setMessage] = useState("");

  const qs = new URLSearchParams({ page: String(page), page_size: String(PAGE), ...(dq && { q: dq }) });
  const { data, isLoading } = useQuery({ queryKey: ["pendingq", qs.toString()], queryFn: () => api<any>(`/api/catalog/revisions/pending?${qs}`), placeholderData: (p) => p });
  const items: any[] = data?.items ?? [];
  useEffect(() => { setSel(new Set()); }, [dq, page]);

  const bulk = useMutation({
    mutationFn: (action: "publish" | "discard") => send("POST", "/api/catalog/revisions/bulk", { table_ids: [...sel], action, message: message || null }),
    onSuccess: (r: any, action) => {
      ["pendingq", "stats", "catalog", "table", "revision", "history", "preview"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
      toast(`${action === "publish" ? "Published" : "Discarded"} ${r.done}${r.failed ? ` · ${r.failed} failed (${r.failed_examples[0]?.reason ?? ""})` : ""}`, !!r.failed);
      setSel(new Set()); setConfirm(null); setMessage("");
    },
    onError: (e) => toast(errText(e), true),
  });
  const pageAll = items.length > 0 && items.every((r) => sel.has(r.table_id));
  const toggle = (id: number) => { const n = new Set(sel); n.has(id) ? n.delete(id) : n.add(id); setSel(n); };

  return (
    <div className="page fill">
      <div className="page-head">
        <div><div className="d-kind"><GitPullRequestDraft className="ic" />Staged edits</div><div className="d-title">Pending changes <InfoTip help={HELP.changes} /></div></div>
      </div>
      <ReviewQueue />
      <div className="toolbar">
        <SearchInput shortcut value={q} onChange={(v) => { setQ(v); setPage(1); }} placeholder="Find a table…" label="Find a table with pending changes" />
        <span className="muted">{data ? `${data.total.toLocaleString()} table${data.total === 1 ? "" : "s"} with pending changes` : ""}</span>
      </div>
      <div className="grid-wrap">
        <table className="grid">
          <thead><tr>
            <th style={{ width: 30 }}>{canEdit && <input type="checkbox" aria-label="Select all on this page" checked={pageAll} onChange={() => setSel(pageAll ? new Set() : new Set(items.map((r) => r.table_id)))} />}</th>
            <th>Table</th><th className="num">Live version</th><th className="num">Changes</th><th>Columns touched</th><th>Edited by</th><th>Updated</th><th style={{ textAlign: "right" }} />
          </tr></thead>
          <tbody>
            {items.map((r) => (
              <tr key={r.table_id} className={sel.has(r.table_id) ? "sel" : ""}>
                <td>{canEdit && <input type="checkbox" aria-label={`Select ${r.table}`} checked={sel.has(r.table_id)} onChange={() => toggle(r.table_id)} />}</td>
                <td><Link className="tname" to={`/tables/${r.table_id}`}>{r.table}</Link></td>
                <td className="num">v{r.version}</td>
                <td className="num">{r.changes}</td>
                <td>{r.columns_touched || <span className="muted">—</span>}</td>
                <td className="sub">{r.contributors.join(", ")}</td>
                <td className="sub">{ago(r.updated_at)}</td>
                <td style={{ textAlign: "right" }}><button className="btn" onClick={() => setReviewing({ id: r.table_id, name: r.table })}><GitPullRequestDraft className="ic" />Review</button></td>
              </tr>
            ))}
            {isLoading && <SkeletonRows rows={6} cols={8} />}
            {data && !items.length && <tr><td colSpan={8}><EmptyState icon={Sparkles} title="Nothing is waiting to be published">When someone edits a published table, the change appears here for review.</EmptyState></td></tr>}
          </tbody>
        </table>
      </div>
      {data && <Pager page={page} pageSize={PAGE} total={data.total} onPage={setPage} />}

      {sel.size > 0 && canEdit && (
        <div className="bulkbar">
          <b>{sel.size} selected</b><span style={{ flex: 1 }} />
          <button className="btn go" onClick={() => setConfirm("publish")}><Send className="ic" />Publish selected</button>
          <button className="btn" onClick={() => setConfirm("discard")}><Undo2 className="ic" />Discard selected</button>
        </div>
      )}
      {reviewing && <PublishDialog tableId={reviewing.id} name={reviewing.name} onClose={() => setReviewing(null)} />}
      {confirm && (
        <Modal title={confirm === "publish" ? `Publish ${sel.size} pending revision${sel.size === 1 ? "" : "s"}?` : `Discard ${sel.size} pending revision${sel.size === 1 ? "" : "s"}?`} width={520} onClose={() => setConfirm(null)}
          footer={<><button className="btn" onClick={() => setConfirm(null)}>Cancel</button><button className={`btn ${confirm === "publish" ? "primary" : "danger-solid"}`} disabled={bulk.isPending} onClick={() => bulk.mutate(confirm)}>{confirm === "publish" ? "Publish" : "Discard"}</button></>}>
          <p style={{ marginTop: 0 }}>{confirm === "publish" ? "Each table goes live as a new version. Any that fail the publishing rules are skipped and reported." : "The pending edits are lost. Live content is not affected."}</p>
          {confirm === "publish" && <div className="field"><label htmlFor="bulk-msg">What changed? (optional, added to each version)</label><input id="bulk-msg" value={message} maxLength={500} onChange={(e) => setMessage(e.target.value)} /></div>}
        </Modal>
      )}
    </div>
  );
}
