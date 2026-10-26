import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, errText, send } from "../../api";
import { Pause, Pencil, Play, Plus, RotateCw, Send, Trash2, Webhook as WebhookIcon, CheckCircle2, AlertTriangle } from "lucide-react";
import { EmptyState, Modal, SkeletonRows, ago, useToast } from "../../ui";
import { Confirm, SecretReveal, Snippet } from "./shared";

function HookForm({ editing, onClose, onCreated }: { editing?: any; onClose: () => void; onCreated: (r: any) => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const meta = useQuery({ queryKey: ["admin-meta"], queryFn: () => api<any>("/api/admin/meta") });
  const [f, setF] = useState({ name: editing?.name ?? "", url: editing?.url ?? "", events: (editing?.events ?? ["table.published", "table.unpublished"]) as string[] });
  const urlOk = /^https?:\/\/[^\s/]+/.test(f.url);
  const save = useMutation({
    mutationFn: () => (editing ? send("PATCH", `/api/admin/webhooks/${editing.id}`, f) : send("POST", "/api/admin/webhooks", f)),
    onSuccess: (r: any) => { qc.invalidateQueries({ queryKey: ["hooks"] }); if (editing) { toast("Webhook updated"); onClose(); } else onCreated(r); },
    onError: (e) => toast(errText(e), true),
  });
  return (
    <Modal title={editing ? `Edit · ${editing.name}` : "Add a webhook"} sub="We call this address when the catalog changes" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!f.name.trim() || !urlOk || !f.events.length || save.isPending} onClick={() => save.mutate()}>{editing ? "Save changes" : "Add webhook"}</button></>}>
      <div className="fields">
        <div className="field"><label htmlFor="hn">Name</label><input id="hn" autoFocus value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="e.g. Chatbot cache refresh" /></div>
        <div className="field"><label htmlFor="hu">Endpoint URL</label><input id="hu" value={f.url} onChange={(e) => setF({ ...f, url: e.target.value })} placeholder="https://your-app.example.com/hooks/semantic-layer" />
          {f.url && !urlOk && <div className="sub" style={{ color: "var(--bad)", marginTop: 3 }}>Must start with http:// or https://</div>}</div>
        <div className="field"><label>Send me…</label>
          <div className="check-list">
            {meta.data?.events.map((e: any) => (
              <label key={e.id} className="check-row"><input type="checkbox" checked={f.events.includes(e.id)} onChange={() => setF({ ...f, events: f.events.includes(e.id) ? f.events.filter((x) => x !== e.id) : [...f.events, e.id] })} /><span><b style={{ fontFamily: "var(--mono)", fontSize: 12.5 }}>{e.id}</b><span className="sub" style={{ display: "block" }}>{e.description}</span></span></label>
            ))}
          </div>
        </div>
      </div>
    </Modal>
  );
}

const VERIFY = `# Verify the signature before trusting a webhook (Python)
import hmac, hashlib

def is_valid(secret: str, raw_body: bytes, header: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header)   # header = X-SL-Signature`;

export default function Webhooks() {
  const qc = useQueryClient();
  const toast = useToast();
  const { data, isLoading } = useQuery({ queryKey: ["hooks"], queryFn: () => api<any[]>("/api/admin/webhooks") });
  const [dlg, setDlg] = useState<{ kind: "add" | "edit" | "delete" | "rotate"; hook?: any } | null>(null);
  const [reveal, setReveal] = useState<{ secret: string; name: string } | null>(null);
  const refresh = () => qc.invalidateQueries({ queryKey: ["hooks"] });
  const test = useMutation({
    mutationFn: (id: number) => send("POST", `/api/admin/webhooks/${id}/test`),
    onSuccess: (r: any) => { refresh(); toast(r.ok ? `Test delivered (${r.status})` : `Test failed: ${r.status}`, !r.ok); },
    onError: (e) => toast(errText(e), true),
  });
  const toggle = useMutation({ mutationFn: (h: any) => send("PATCH", `/api/admin/webhooks/${h.id}`, { is_active: !h.is_active }), onSuccess: refresh });
  const act = useMutation({
    mutationFn: ({ kind, id }: { kind: string; id: number }) => (kind === "delete" ? send("DELETE", `/api/admin/webhooks/${id}`) : send("POST", `/api/admin/webhooks/${id}/rotate-secret`)),
    onSuccess: (r: any, v) => { refresh(); setDlg(null); if (v.kind === "rotate") setReveal({ secret: r.secret, name: r.webhook.name }); else toast("Webhook deleted"); },
    onError: (e) => toast(errText(e), true),
  });
  const list = data ?? [];
  return (
    <>
      <section className="card">
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <h3><WebhookIcon className="ic" />Webhooks</h3>
            <p className="hint" style={{ marginBottom: 0 }}>Tell other applications when something changes — for example, so a chatbot can refresh its cached view when a table is published. Each call is signed so the receiver can verify it came from here.</p>
          </div>
          <button className="btn primary" onClick={() => setDlg({ kind: "add" })}><Plus className="ic" />Add webhook</button>
        </div>
        <div className="grid-wrap" style={{ marginTop: 14 }}>
          <table className="grid">
            <thead><tr><th>Webhook</th><th>Events</th><th>Last delivery</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {list.map((h) => (
                <tr key={h.id} style={!h.is_active ? { opacity: 0.6 } : undefined}>
                  <td><b style={{ color: "var(--petrol)" }}>{h.name}</b>{!h.is_active && <span className="chip" style={{ marginInlineStart: 8 }}>paused</span>}<div className="sub" style={{ fontFamily: "var(--mono)", wordBreak: "break-all" }}>{h.url}</div><div className="sub">Secret {h.secret_hint}</div></td>
                  <td><div className="chips" style={{ margin: 0 }}>{h.events.map((e: string) => <span key={e} className="chip">{e}</span>)}</div></td>
                  <td>{h.last_delivery_at ? <><span className={`chip with-ic ${h.last_status?.startsWith("2") ? "ok" : "warn"}`}>{h.last_status?.startsWith("2") ? <CheckCircle2 className="ic" /> : <AlertTriangle className="ic" />}{h.last_status}</span><div className="sub">{ago(h.last_delivery_at)}</div></> : <span className="muted">never</span>}</td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    <button className="btn" disabled={test.isPending} onClick={() => test.mutate(h.id)}>{test.isPending && test.variables === h.id ? <><RotateCw className="ic spin" />Sending…</> : <><Send className="ic" />Send test</>}</button>{" "}
                    <button className="btn" onClick={() => setDlg({ kind: "edit", hook: h })}><Pencil className="ic" />Edit</button>{" "}
                    <button className="btn" onClick={() => toggle.mutate(h)}>{h.is_active ? <><Pause className="ic" />Pause</> : <><Play className="ic" />Resume</>}</button>{" "}
                    <button className="btn" onClick={() => setDlg({ kind: "rotate", hook: h })}><RotateCw className="ic" />New secret</button>{" "}
                    <button className="btn danger" onClick={() => setDlg({ kind: "delete", hook: h })}><Trash2 className="ic" />Delete</button>
                  </td>
                </tr>
              ))}
              {isLoading && <SkeletonRows rows={2} cols={4} />}
              {!isLoading && !list.length && <tr><td colSpan={4}><EmptyState icon={WebhookIcon} title="No webhooks yet" actions={<button className="btn primary" onClick={() => setDlg({ kind: "add" })}><Plus className="ic" />Add webhook</button>}>Notify other applications when tables are published or a sync finishes.</EmptyState></td></tr>}
            </tbody>
          </table>
        </div>
      </section>
      <section className="card">
        <h3><Send className="ic" />Receiving a webhook</h3>
        <p className="hint">Each call is a JSON <code>POST</code> with headers <code>X-SL-Event</code> and <code>X-SL-Signature</code>. Deliveries are best-effort (one attempt, 5-second timeout) — treat them as a nudge to re-read the catalog, not as the only source of truth.</p>
        <Snippet title="Verify the signature" code={VERIFY} />
      </section>

      {dlg?.kind === "add" && <HookForm onClose={() => setDlg(null)} onCreated={(r) => { setDlg(null); setReveal({ secret: r.secret, name: r.webhook.name }); }} />}
      {dlg?.kind === "edit" && <HookForm editing={dlg.hook} onClose={() => setDlg(null)} onCreated={() => {}} />}
      {dlg?.kind === "rotate" && <Confirm title={`New secret for “${dlg.hook.name}”?`} confirmLabel="Generate new secret" busy={act.isPending} onClose={() => setDlg(null)} onConfirm={() => act.mutate({ kind: "rotate", id: dlg.hook.id })}>Deliveries are signed with the new secret straight away. Update the receiving application, or it will reject them.</Confirm>}
      {dlg?.kind === "delete" && <Confirm title={`Delete “${dlg.hook.name}”?`} danger confirmLabel="Delete" busy={act.isPending} onClose={() => setDlg(null)} onConfirm={() => act.mutate({ kind: "delete", id: dlg.hook.id })}>It stops receiving events immediately.</Confirm>}
      {reveal && <SecretReveal title={`Signing secret · ${reveal.name}`} secret={reveal.secret} onClose={() => setReveal(null)} hint="Give this to the receiving application so it can verify signatures. It is shown only now." />}
    </>
  );
}
