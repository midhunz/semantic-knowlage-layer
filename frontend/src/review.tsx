import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ArrowRight, Check, EyeOff, Pencil, Send, Undo2, X } from "lucide-react";
import { api, errText, send } from "./api";
import { useAuth } from "./auth";
import { Modal, ago, useToast } from "./ui";
import { fmtVal } from "./revisions";

/** draft → review → published for dimensions, metrics and glossary terms (backend: services/review.py). */
export type Kind = "dimension" | "metric" | "glossary";
export const KIND_LABEL: Record<Kind, string> = { dimension: "Dimension", metric: "Metric", glossary: "Glossary term" };

const QUERY_KEYS = ["dimensions", "dimension", "metrics", "glossary", "review", "stats", "table", "preview"];

export function useReview(kind: Kind) {
  const qc = useQueryClient();
  const toast = useToast();
  const refresh = () => QUERY_KEYS.forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  const act = useMutation({
    mutationFn: ({ id, action, note }: { id: number; action: string; note?: string }) =>
      action === "discard" ? send("DELETE", `/api/review/${kind}/${id}/draft`) : send("POST", `/api/review/${kind}/${id}/${action}`, action === "reject" ? { note } : undefined),
    onSuccess: (_r, v) => { refresh(); toast({ submit: "Submitted for review", approve: "Approved — it is live", reject: "Sent back to draft", unpublish: "Withdrawn from agents", discard: "Draft discarded", "edit-draft": "Draft started — agents still see the live version" }[v.action] ?? "Done"); },
    onError: (e) => toast(errText(e), true),
  });
  return act;
}

export function RejectDialog({ name, busy, onClose, onReject }: { name: string; busy: boolean; onClose: () => void; onReject: (note: string) => void }) {
  const [note, setNote] = useState("");
  return (
    <Modal title={`Reject “${name}”`} sub="It goes back to draft with your note so the author can fix it" onClose={onClose} width={520}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className="btn danger" disabled={!note.trim() || busy} onClick={() => onReject(note.trim())}><X className="ic" />Reject</button></>}>
      <div className="field"><label htmlFor="rj">Why?</label><textarea id="rj" autoFocus rows={4} value={note} onChange={(e) => setNote(e.target.value)} /></div>
    </Modal>
  );
}

/**
 * The buttons and notes for one item. `item` needs id, status, name, draft_of_id (set on a draft copy),
 * draft_id (set on a live item that has one) and review_note. `onOpen(id)` is called with the id to edit.
 */
export function ReviewBar({ kind, item, name, onOpen, onGone }: { kind: Kind; item: any; name: string; onOpen?: (id: number) => void; onGone?: () => void }) {
  const { canEdit } = useAuth();
  const act = useReview(kind);
  const [rejecting, setRejecting] = useState(false);
  const isCopy = !!item.draft_of_id;
  const go = (action: string, note?: string, after?: (r: any) => void) => act.mutate({ id: item.id, action, note }, { onSuccess: (r) => { setRejecting(false); after?.(r); } });
  return (
    <div className="review-bar">
      {item.status === "published" && <div className="banner"><Send className="ic" />Live: agents read this version. Changes are made in a draft that a reviewer approves.</div>}
      {isCopy && item.status !== "published" && <div className="banner"><Pencil className="ic" />Draft of the live version. Agents still see the live one until this is approved.</div>}
      {item.status === "review" && <div className="banner"><Send className="ic" />Waiting for a reviewer{item.submitted_by ? ` (submitted by ${item.submitted_by})` : ""}.</div>}
      {item.review_note && item.status === "draft" && <div className="banner bad" role="alert"><X className="ic" />Rejected: {item.review_note}</div>}
      {canEdit && (
        <div className="d-actions">
          {item.status === "published" && (<>
            <button className="btn primary" disabled={act.isPending} onClick={() => go("edit-draft", undefined, (r) => onOpen?.(r.id))}><Pencil className="ic" />{item.draft_id ? "Open the draft" : "Edit as draft"}</button>
            <button className="btn" disabled={act.isPending} onClick={() => window.confirm(`Withdraw “${name}” from agents now?`) && go("unpublish")}><EyeOff className="ic" />Unpublish</button>
          </>)}
          {item.status === "draft" && <button className="btn primary" disabled={act.isPending} onClick={() => go("submit")}><Send className="ic" />Submit for review</button>}
          {item.status === "review" && (<>
            <button className="btn primary" disabled={act.isPending} onClick={() => go("approve", undefined, (r) => isCopy && onOpen?.(r.id))}><Check className="ic" />Approve</button>
            <button className="btn danger" disabled={act.isPending} onClick={() => setRejecting(true)}><X className="ic" />Reject</button>
          </>)}
          {isCopy && item.status !== "published" && <button className="btn" disabled={act.isPending} onClick={() => window.confirm("Discard this draft? The live version is not affected.") && go("discard", undefined, () => onGone?.())}><Undo2 className="ic" />Discard draft</button>}
        </div>
      )}
      {rejecting && <RejectDialog name={name} busy={act.isPending} onClose={() => setRejecting(false)} onReject={(note) => go("reject", note)} />}
    </div>
  );
}

/** What changed in an item under review (backend: review.diff). */
export function ReviewDiff({ diff }: { diff: any }) {
  const v = diff.values ?? {};
  const b = diff.bindings ?? {};
  const lists: [string, string[] | undefined][] = [["Values added", v.added], ["Values removed", v.removed], ["Values edited", v.changed], ["Columns linked", b.added], ["Columns unlinked", b.removed]];
  const any = diff.fields?.length || lists.some(([, l]) => l?.length);
  return (
    <div className="diff-list">
      {diff.new && <p className="muted" style={{ margin: "0 0 6px" }}>New — not live yet.</p>}
      {diff.fields?.map((f: any) => (
        <div className="diff-row" key={f.field}>
          <div className="diff-what"><b>{f.field.replace(/_ar$/, " (Arabic)").replace(/_/g, " ")}</b></div>
          <div className="diff-vals">
            <span className="old" dir="auto">{fmtVal(f.old) || <i className="muted">empty</i>}</span><ArrowRight className="ic" /><span className="new" dir="auto">{fmtVal(f.new) || <i className="muted">empty</i>}</span>
          </div>
        </div>
      ))}
      {lists.filter(([, l]) => l?.length).map(([label, l]) => (
        <div className="diff-row" key={label}><div className="diff-what"><b>{label}</b></div><div className="diff-vals"><span className="new">{l!.join(", ")}</span></div></div>
      ))}
      {!any && !diff.new && <p className="muted" style={{ margin: 0 }}>No differences from the live version.</p>}
    </div>
  );
}

const LINK: Record<Kind, (id: number) => string> = {
  dimension: (id) => `/dimensions/${id}`,
  metric: (id) => `/metrics?open=${id}`,
  glossary: () => `/glossary`,
};

/** Dimensions, metrics and glossary terms waiting for a reviewer, with what changed. */
export function ReviewQueue() {
  const { canEdit } = useAuth();
  const q = useQuery({ queryKey: ["review"], queryFn: () => api<any>("/api/review") });
  const run = useMutation({
    mutationFn: ({ kind, id, action, note }: { kind: Kind; id: number; action: string; note?: string }) =>
      send("POST", `/api/review/${kind}/${id}/${action}`, action === "reject" ? { note } : undefined),
    onSuccess: (_r, v) => { ["review", "dimensions", "dimension", "metrics", "glossary"].forEach((k) => qc.invalidateQueries({ queryKey: [k] })); toast(v.action === "approve" ? "Approved — it is live" : "Sent back to draft"); setRejecting(null); },
    onError: (e) => toast(errText(e), true),
  });
  const qc = useQueryClient();
  const toast = useToast();
  const [rejecting, setRejecting] = useState<any>(null);
  const items: any[] = q.data?.items ?? [];
  if (!items.length) return null;
  return (
    <section className="card" style={{ margin: "0 0 16px" }}>
      <h3>Awaiting review <span className="count-pill">{items.length}</span></h3>
      {items.map((it) => (
        <div className="list-row" key={`${it.kind}-${it.id}`}>
          <div className="lr-main">
            <div className="lr-title">
              <span className="chip">{KIND_LABEL[it.kind as Kind]}</span>{" "}
              <Link className="tname" to={LINK[it.kind as Kind](it.id)}>{it.name}</Link>
              <span className="sub"> · {it.live_id ? "change to a live item" : "new"}{it.submitted_by ? ` · by ${it.submitted_by}` : ""} · {ago(it.submitted_at)}</span>
            </div>
            <ReviewDiff diff={it.diff} />
          </div>
          {canEdit && (
            <div className="d-actions">
              <button className="btn primary" disabled={run.isPending} onClick={() => run.mutate({ kind: it.kind, id: it.id, action: "approve" })}><Check className="ic" />Approve</button>
              <button className="btn danger" disabled={run.isPending} onClick={() => setRejecting(it)}><X className="ic" />Reject</button>
            </div>
          )}
        </div>
      ))}
      {rejecting && <RejectDialog name={rejecting.name} busy={run.isPending} onClose={() => setRejecting(null)} onReject={(note) => run.mutate({ kind: rejecting.kind, id: rejecting.id, action: "reject", note })} />}
    </section>
  );
}
