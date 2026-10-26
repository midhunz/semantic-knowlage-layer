import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, GitPullRequestDraft, History as HistoryIcon, Send, Undo2, RotateCcw } from "lucide-react";
import { api, errText, send } from "./api";
import { useAuth } from "./auth";
import { EmptyState, Modal, ago, when, useToast } from "./ui";

/** A semantic value shown in a diff: empty, text, list, map or flag. */
export function fmtVal(v: unknown): string {
  if (v === null || v === undefined || v === "" || (Array.isArray(v) && !v.length)) return "";
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (Array.isArray(v)) return v.join(", ");
  if (typeof v === "object") return Object.entries(v as object).map(([k, x]) => `${k}=${x}`).join("; ");
  return String(v);
}

const label = (f: string) => f.replace(/_ar$/, " (Arabic)").replace(/_/g, " ");

export type DiffRow = { scope: "table" | "column"; column: string | null; field: string; old: unknown; new: unknown };

export function DiffList({ diff }: { diff: DiffRow[] }) {
  if (!diff.length) return <p className="muted" style={{ margin: 0 }}>No differences.</p>;
  return (
    <div className="diff-list">
      {diff.map((d, i) => (
        <div className="diff-row" key={i}>
          <div className="diff-what">
            <span className={`chip with-ic ${d.scope === "table" ? "info" : ""}`}>{d.scope === "table" ? "Table" : <code>{d.column}</code>}</span>
            <b>{label(d.field)}</b>
          </div>
          <div className="diff-vals">
            <span className="old" dir="auto">{fmtVal(d.old) || <i className="muted">empty</i>}</span>
            <ArrowRight className="ic" />
            <span className="new" dir="auto">{fmtVal(d.new) || <i className="muted">empty</i>}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export function useRefreshAll() {
  const qc = useQueryClient();
  return () => ["table", "revision", "history", "catalog", "stats", "tree", "pendingq", "quarantine", "preview"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
}

/** Review the pending changes of one table, then publish them as a new version or discard them. */
export function PublishDialog({ tableId, name, onClose }: { tableId: number | string; name: string; onClose: () => void }) {
  const toast = useToast();
  const refresh = useRefreshAll();
  const { canEdit } = useAuth();
  const [message, setMessage] = useState("");
  const { data, isLoading } = useQuery({ queryKey: ["revision", String(tableId)], queryFn: () => api<any>(`/api/tables/${tableId}/revision`) });
  const publish = useMutation({
    mutationFn: () => send("POST", `/api/tables/${tableId}/revision/publish`, { message: message || null }),
    onSuccess: (r: any) => { refresh(); toast(`Published as version ${r.version} — agents now see it`); onClose(); },
    onError: (e) => toast(errText(e), true),
  });
  const discard = useMutation({
    mutationFn: () => send("DELETE", `/api/tables/${tableId}/revision`),
    onSuccess: () => { refresh(); toast("Pending changes discarded"); onClose(); },
    onError: (e) => toast(errText(e), true),
  });
  const p = data?.pending;
  return (
    <Modal title="Review pending changes" sub={`${name} · agents currently see version ${data?.version ?? "…"}`} onClose={onClose} width={760}
      footer={canEdit && p ? (
        <>
          <button className="btn danger" disabled={discard.isPending || publish.isPending} onClick={() => window.confirm("Discard all pending changes to this table? This cannot be undone.") && discard.mutate()}><Undo2 className="ic" />Discard</button>
          <div className="spacer" />
          <button className="btn" onClick={onClose}>Close</button>
          <button className="btn primary" disabled={publish.isPending || discard.isPending} onClick={() => publish.mutate()}><Send className="ic" />{publish.isPending ? "Publishing…" : `Publish as version ${(data?.version ?? 0) + 1}`}</button>
        </>
      ) : <button className="btn" onClick={onClose}>Close</button>}>
      {isLoading && <div className="loading">Loading…</div>}
      {data && !p && <EmptyState icon={GitPullRequestDraft} title="No pending changes">Everything is live.</EmptyState>}
      {p && (
        <>
          <div className="chips" style={{ margin: "0 0 12px" }}>
            <span className="chip with-ic"><GitPullRequestDraft className="ic" />{p.count} change{p.count === 1 ? "" : "s"}</span>
            <span className="chip">edited by {p.contributors.join(", ")}</span>
            <span className="chip">updated {ago(p.updated_at)}</span>
          </div>
          <DiffList diff={data.diff} />
          {canEdit && (
            <div className="field" style={{ marginTop: 16 }}>
              <label htmlFor="rev-msg">What changed? (optional, shown in the history)</label>
              <input id="rev-msg" value={message} maxLength={500} onChange={(e) => setMessage(e.target.value)} placeholder="e.g. Clarified the grain after the finance review" />
            </div>
          )}
        </>
      )}
    </Modal>
  );
}

/** Published versions of a table: see what each changed, and stage a restore of any of them. */
export function HistoryPanel({ tableId }: { tableId: string }) {
  const toast = useToast();
  const refresh = useRefreshAll();
  const { canEdit } = useAuth();
  const [open, setOpen] = useState<number | null>(null);
  const { data } = useQuery({ queryKey: ["history", tableId], queryFn: () => api<any>(`/api/tables/${tableId}/revisions`) });
  const detail = useQuery({ queryKey: ["history", tableId, open], enabled: open != null, queryFn: () => api<any>(`/api/tables/${tableId}/revisions/${open}`) });
  const restore = useMutation({
    mutationFn: ({ n, replace }: { n: number; replace: boolean }) => send("POST", `/api/tables/${tableId}/revisions/${n}/restore`, { replace }),
    onSuccess: (r: any) => { refresh(); toast(r.staged ? `Version ${r.from_version} staged for review — publish it to make it live` : `Version ${r.from_version} restored`); },
    onError: (e, v) => {
      const msg = errText(e);
      if (msg.startsWith("There are already pending") && window.confirm("This table already has pending changes. Replace them with the restore?")) restore.mutate({ n: v.n, replace: true });
      else toast(msg, true);
    },
  });
  if (!data) return <div className="loading">Loading…</div>;
  if (!data.items.length) return <EmptyState icon={HistoryIcon} title="No versions yet">A version is recorded when the table is published, and again each time its changes are published.</EmptyState>;
  return (
    <div>
      {data.items.map((h: any) => (
        <div className="ver" key={h.number}>
          <div className="ver-head" onClick={() => setOpen(open === h.number ? null : h.number)} role="button" tabIndex={0}
            onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), setOpen(open === h.number ? null : h.number))}>
            <span className={`chip with-ic ${h.number === data.version ? "ok" : ""}`}>v{h.number}{h.number === data.version && " · live"}</span>
            <b style={{ flex: 1 }}>{h.message || "Published"}</b>
            <span className="muted" title={when(h.published_at)}>{h.published_by} · {ago(h.published_at)}</span>
            <span className="chip">{h.changes} change{h.changes === 1 ? "" : "s"}</span>
          </div>
          {open === h.number && (
            <div className="ver-body">
              {detail.isLoading ? <div className="loading">Loading…</div> : (
                <>
                  <h4>What this version changed</h4>
                  {detail.data?.diff.length ? <DiffList diff={detail.data.diff} /> : <p className="muted">First version, or no content changes.</p>}
                  {h.number !== data.version && (
                    <>
                      <h4 style={{ marginTop: 16 }}>Restoring it would change the live content like this</h4>
                      <DiffList diff={detail.data?.restore_preview ?? []} />
                      {canEdit && <div style={{ marginTop: 12 }}><button className="btn" disabled={restore.isPending} onClick={() => restore.mutate({ n: h.number, replace: false })}><RotateCcw className="ic" />Stage a restore of v{h.number}</button> <span className="muted">It is reviewed and published like any other change.</span></div>}
                    </>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
