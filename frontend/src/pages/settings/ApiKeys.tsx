import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, errText, send } from "../../api";
import { Modal, ago, useToast, when } from "../../ui";
import { AlertTriangle, Plug, Ban, CheckCircle2, KeyRound, Pencil, Plus, RotateCw, Trash2, XCircle, Clock } from "lucide-react";
import { Confirm, SecretReveal, Snippet } from "./shared";
import { EmptyState, SkeletonRows } from "../../ui";

const EXPIRY = [["", "Never"], ["30", "30 days"], ["90", "90 days"], ["365", "1 year"]];
const SCOPE_LABEL: Record<string, string> = { "agent:read": "Agent read", "catalog:read": "Catalog read", "catalog:write": "Catalog write" };

function KeyForm({ editing, onClose, onCreated }: { editing?: any; onClose: () => void; onCreated: (r: any) => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const meta = useQuery({ queryKey: ["admin-meta"], queryFn: () => api<any>("/api/admin/meta") });
  const facets = useQuery({ queryKey: ["facets"], queryFn: () => api<any>("/api/catalog/facets") });
  const [f, setF] = useState({ name: editing?.name ?? "", description: editing?.description ?? "", scopes: (editing?.scopes ?? ["agent:read"]) as string[], domains: (editing?.allowed_domains ?? []) as string[], expires: "" });
  const toggle = (list: string[], v: string) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  const body = { name: f.name.trim(), description: f.description || null, scopes: f.scopes, allowed_domains: f.domains };
  const save = useMutation({
    mutationFn: () => (editing ? send("PATCH", `/api/admin/keys/${editing.id}`, body) : send("POST", "/api/admin/keys", { ...body, expires_in_days: f.expires ? Number(f.expires) : null })),
    onSuccess: (r: any) => { qc.invalidateQueries({ queryKey: ["keys"] }); if (editing) { toast("API key updated"); onClose(); } else onCreated(r); },
    onError: (e) => toast(errText(e), true),
  });
  const domains: string[] = facets.data?.domains.map((d: any) => d.value) ?? [];
  return (
    <Modal title={editing ? `Edit · ${editing.name}` : "Create an API key"} sub="One key per application, so you can cut off one without breaking the rest" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!f.name.trim() || !f.scopes.length || save.isPending} onClick={() => save.mutate()}>{editing ? "Save changes" : <><KeyRound className="ic" />Create key</>}</button></>}>
      <div className="fields">
        <div className="field"><label htmlFor="kn">Application name</label><input id="kn" autoFocus value={f.name} maxLength={100} onChange={(e) => setF({ ...f, name: e.target.value })} placeholder="e.g. Support chatbot" /></div>
        <div className="field"><label htmlFor="kd">Notes (optional)</label><input id="kd" value={f.description} maxLength={500} onChange={(e) => setF({ ...f, description: e.target.value })} placeholder="Who owns it, where it runs" /></div>
        <div className="field">
          <label>What can it do?</label>
          <div className="check-list">
            {meta.data?.scopes.map((s: any) => (
              <label key={s.id} className="check-row"><input type="checkbox" checked={f.scopes.includes(s.id)} onChange={() => setF({ ...f, scopes: toggle(f.scopes, s.id) })} /><span><b>{SCOPE_LABEL[s.id] ?? s.id}</b><span className="sub" style={{ display: "block" }}>{s.description}</span></span></label>
            ))}
          </div>
        </div>
        <div className="field">
          <label>Which data can it see?</label>
          <div className="check-list">
            <label className="check-row"><input type="radio" name="dom" checked={f.domains.length === 0} onChange={() => setF({ ...f, domains: [] })} /><span><b>All domains</b></span></label>
            <label className="check-row"><input type="radio" name="dom" checked={f.domains.length > 0} onChange={() => setF({ ...f, domains: f.domains.length ? f.domains : domains.slice(0, 1) })} disabled={!domains.length} /><span><b>Only selected domains</b><span className="sub" style={{ display: "block" }}>{domains.length ? "Tables outside these domains don't exist as far as this key is concerned." : "Give tables a domain first (Catalog → set domain)."}</span></span></label>
          </div>
          {f.domains.length > 0 && <div className="chips" style={{ marginTop: 8 }}>{domains.map((d) => <button type="button" key={d} className={`pill${f.domains.includes(d) ? " on" : ""}`} onClick={() => setF({ ...f, domains: toggle(f.domains, d) })}>{d}</button>)}</div>}
        </div>
        {!editing && (
          <div className="field" style={{ maxWidth: 220 }}><label htmlFor="ke">Expires</label>
            <select id="ke" value={f.expires} onChange={(e) => setF({ ...f, expires: e.target.value })}>{EXPIRY.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
        )}
      </div>
    </Modal>
  );
}

export function QuickStart({ secret }: { secret?: string }) {
  const base = window.location.origin;
  const key = secret ?? "YOUR_API_KEY";
  return (
    <div className="snips">
      <Snippet title="curl — search, then read a table" code={`curl -H "X-API-Key: ${key}" "${base}/agent/search?q=revenue&lang=both"\n\ncurl -H "X-API-Key: ${key}" "${base}/agent/tables/SOURCE.SCHEMA.TABLE/context?lang=ar&max_tokens=2000"`} />
      <Snippet title="Python" code={`import requests\n\nAPI = "${base}"\nHEADERS = {"X-API-Key": "${key}"}\n\nctx = requests.get(f"{API}/agent/export", params={"domain": "sales", "lang": "both"}, headers=HEADERS).text\n# put \`ctx\` in your agent's system prompt`} />
      <Snippet title="MCP (Claude Desktop, Cursor, …) — runs on a machine that can read the catalog database" code={`{\n  "mcpServers": {\n    "semantic-layer": {\n      "command": "/path/to/backend/.venv/bin/python",\n      "args": ["-m", "app.mcp_server"],\n      "env": { "SL_DATABASE_URL": "<same database URL as the API>" }\n    }\n  }\n}`} />
    </div>
  );
}

export default function ApiKeys() {
  const qc = useQueryClient();
  const toast = useToast();
  const { data, isLoading } = useQuery({ queryKey: ["keys"], queryFn: () => api<any[]>("/api/admin/keys") });
  const [dlg, setDlg] = useState<{ kind: "create" | "edit" | "revoke" | "rotate" | "delete"; key?: any } | null>(null);
  const [reveal, setReveal] = useState<{ secret: string; name: string; rotated?: boolean } | null>(null);
  const refresh = () => qc.invalidateQueries({ queryKey: ["keys"] });
  const act = useMutation({
    mutationFn: ({ kind, id }: { kind: string; id: number }) => (kind === "delete" ? send("DELETE", `/api/admin/keys/${id}`) : send("POST", `/api/admin/keys/${id}/${kind}`)),
    onSuccess: (r: any, v) => {
      refresh(); setDlg(null);
      if (v.kind === "rotate") setReveal({ secret: r.secret, name: r.key.name, rotated: true });
      else toast(v.kind === "revoke" ? "Key revoked — it no longer works" : "Key deleted");
    },
    onError: (e) => toast(errText(e), true),
  });
  const list = data ?? [];

  return (
    <>
      <section className="card">
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <h3><KeyRound className="ic" />API keys</h3>
            <p className="hint" style={{ marginBottom: 0 }}>Let other applications — chatbots, agents, dashboards, pipelines — use the semantic layer. Secrets are shown once and stored only as a hash.</p>
          </div>
          <button className="btn primary" onClick={() => setDlg({ kind: "create" })}><Plus className="ic" />Create key</button>
        </div>
        <div className="grid-wrap" style={{ marginTop: 14 }}>
          <table className="grid">
            <thead><tr><th>Application</th><th>Key</th><th>Access</th><th>Status</th><th>Last used</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {list.map((k) => (
                <tr key={k.id} style={k.status !== "active" ? { opacity: 0.6 } : undefined}>
                  <td><b style={{ color: "var(--petrol)" }}>{k.name}</b>{k.description && <div className="sub">{k.description}</div>}<div className="sub">Created {ago(k.created_at)}{k.created_by ? ` by ${k.created_by}` : ""}</div></td>
                  <td><code className="sub" style={{ fontFamily: "var(--mono)" }}>{k.prefix}…</code></td>
                  <td>
                    <div className="chips" style={{ margin: 0 }}>{k.scopes.map((s: string) => <span className="chip" key={s}>{SCOPE_LABEL[s] ?? s}</span>)}</div>
                    <div className="sub" style={{ marginTop: 4 }}>{k.allowed_domains.length ? `Domains: ${k.allowed_domains.join(", ")}` : "All domains"}</div>
                  </td>
                  <td><span className={`chip with-ic ${k.status === "active" ? "ok" : "warn"}`}>{k.status === "active" ? <CheckCircle2 className="ic" /> : k.status === "expired" ? <Clock className="ic" /> : <XCircle className="ic" />}{k.status}</span>{k.expires_at && k.status === "active" && <div className="sub">expires {when(k.expires_at)}</div>}</td>
                  <td>{k.last_used_at ? ago(k.last_used_at) : <span className="muted">never</span>}<div className="sub">{k.use_count.toLocaleString()} calls</div></td>
                  <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                    <button className="btn" onClick={() => setDlg({ kind: "edit", key: k })}><Pencil className="ic" />Edit</button>{" "}
                    <button className="btn" onClick={() => setDlg({ kind: "rotate", key: k })} title="Issue a new secret; the old one stops working"><RotateCw className="ic" />Rotate</button>{" "}
                    {k.status === "active" && <><button className="btn danger" onClick={() => setDlg({ kind: "revoke", key: k })}><Ban className="ic" />Revoke</button>{" "}</>}
                    <button className="btn danger" onClick={() => setDlg({ kind: "delete", key: k })}><Trash2 className="ic" />Delete</button>
                  </td>
                </tr>
              ))}
              {isLoading && <SkeletonRows rows={3} cols={6} />}
              {!isLoading && !list.length && <tr><td colSpan={6}><EmptyState icon={KeyRound} title="No API keys yet" actions={<button className="btn primary" onClick={() => setDlg({ kind: "create" })}><Plus className="ic" />Create key</button>}>Create one for the first application that needs to read the semantic layer.</EmptyState></td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h3><Plug className="ic" />Connect an application</h3>
        <p className="hint">Replace <code>YOUR_API_KEY</code> with a key from above. Agents only ever see <b>published</b> tables.</p>
        <QuickStart />
      </section>

      {dlg?.kind === "create" && <KeyForm onClose={() => setDlg(null)} onCreated={(r) => { setDlg(null); setReveal({ secret: r.secret, name: r.key.name }); }} />}
      {dlg?.kind === "edit" && <KeyForm editing={dlg.key} onClose={() => setDlg(null)} onCreated={() => {}} />}
      {dlg?.kind === "revoke" && <Confirm title={`Revoke “${dlg.key.name}”?`} danger confirmLabel="Revoke key" busy={act.isPending} onClose={() => setDlg(null)} onConfirm={() => act.mutate({ kind: "revoke", id: dlg.key.id })}>The application using this key will immediately get “unauthorized”. You can't undo this, but you can create a new key.</Confirm>}
      {dlg?.kind === "rotate" && <Confirm title={`Rotate “${dlg.key.name}”?`} confirmLabel="Rotate and show new key" busy={act.isPending} onClose={() => setDlg(null)} onConfirm={() => act.mutate({ kind: "rotate", id: dlg.key.id })}>A new secret is issued and the current one <b>stops working immediately</b>. Update the application right after.</Confirm>}
      {dlg?.kind === "delete" && <Confirm title={`Delete “${dlg.key.name}”?`} danger confirmLabel="Delete" busy={act.isPending} onClose={() => setDlg(null)} onConfirm={() => act.mutate({ kind: "delete", id: dlg.key.id })}>The key stops working and its usage record is removed.</Confirm>}
      {reveal && (
        <SecretReveal title={reveal.rotated ? `New key for ${reveal.name}` : `Key created · ${reveal.name}`} secret={reveal.secret} onClose={() => setReveal(null)}
          hint="Copy this key now. For your security it is stored only as a hash and can never be shown again.">
          <QuickStart secret={reveal.secret} />
        </SecretReveal>
      )}
    </>
  );
}
