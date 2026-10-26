import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, send } from "../api";
import { AlertTriangle, CheckCircle2, Database, Pencil, Plug, Plus, RefreshCw, Trash2, XCircle } from "lucide-react";
import { useAuth } from "../auth";
import { EmptyState, Modal, SkeletonRows, useTitle, useToast, InfoTip } from "../ui";
import { HELP } from "../help";

type Form = { name: string; host: string; port: string; catalog: string; user: string; http_scheme: string; password_env: string };
const BLANK: Form = { name: "", host: "localhost", port: "8080", catalog: "", user: "catalog", http_scheme: "http", password_env: "" };

const toForm = (s: any): Form => ({
  name: s.name, host: s.config.host ?? "", port: String(s.config.port ?? 8080), catalog: s.config.catalog ?? "",
  user: s.config.user ?? "", http_scheme: s.config.http_scheme ?? "http", password_env: s.config.password_env ?? "",
});
const toBody = (f: Form, base: object = {}) => ({
  name: f.name.trim(), kind: "trino",
  config: { ...base, host: f.host.trim(), port: Number(f.port), catalog: f.catalog.trim(), user: f.user.trim(), http_scheme: f.http_scheme,
    ...(f.password_env.trim() ? { password_env: f.password_env.trim() } : {}) },
});
const errMsg = (e: unknown) => String((e as Error).message ?? e).replace(/^\d+:\s*/, "").replace(/^\{"detail":"?|"?\}$/g, "");

function SourceForm({ initial, editing, onClose }: { initial: Form; editing?: any; onClose: () => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [f, setF] = useState<Form>(initial);
  const [test, setTest] = useState<{ ok: boolean; msg: string } | null>(null);
  const set = (k: keyof Form) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => { setF({ ...f, [k]: e.target.value }); setTest(null); };
  const body = toBody(f, editing?.config);
  const valid = /^[A-Za-z0-9][A-Za-z0-9_-]*$/.test(f.name.trim()) && f.host.trim() && f.catalog.trim() && f.user.trim() && Number(f.port) > 0;

  const check = useMutation({
    mutationFn: () => send("POST", "/api/sources/test", body),
    onSuccess: (r: any) => setTest({ ok: true, msg: r.detail }),
    onError: (e) => setTest({ ok: false, msg: errMsg(e) }),
  });
  const save = useMutation({
    mutationFn: () => (editing ? send("PUT", `/api/sources/${editing.id}`, body) : send("POST", "/api/sources", body)),
    onSuccess: () => { ["sources", "tree", "stats", "catalog"].forEach((k) => qc.invalidateQueries({ queryKey: [k] })); toast(editing ? "Source updated" : "Source added — now sync it"); onClose(); },
    onError: (e) => setTest({ ok: false, msg: errMsg(e) }),
  });

  const field = (k: keyof Form, label: string, hint?: string, type = "text") => (
    <div className="field"><label htmlFor={`src-${k}`}>{label}</label><input id={`src-${k}`} type={type} value={f[k]} onChange={set(k)} />{hint && <div className="sub" style={{ marginTop: 3 }}>{hint}</div>}</div>
  );
  return (
    <Modal title={editing ? `Edit source · ${editing.name}` : "Add a data lake source"} sub="Trino (Iceberg, Hive, Delta…) — use a read-only user" onClose={onClose}
      footer={<>
        <button className="btn" disabled={!valid || check.isPending} onClick={() => check.mutate()}>{check.isPending ? <RefreshCw className="ic spin" /> : <Plug className="ic" />}{check.isPending ? "Testing…" : "Test connection"}</button>
        <div className="spacer" />
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn primary" disabled={!valid || save.isPending} onClick={() => save.mutate()}>{editing ? "Save changes" : "Add source"}</button>
      </>}>
      <div className="fields">
        {field("name", "Source name", "Letters, numbers, - and _ only. Agents see tables as name.schema.table.")}
        <div className="two-col">{field("host", "Host")}{field("port", "Port", undefined, "number")}</div>
        <div className="two-col">{field("catalog", "Trino catalog", "e.g. lake, iceberg, hive")}{field("user", "User")}</div>
        <div className="two-col">
          <div className="field"><label htmlFor="src-proto">Protocol</label><select id="src-proto" value={f.http_scheme} onChange={set("http_scheme")}><option value="http">http</option><option value="https">https</option></select></div>
          {field("password_env", "Password env variable (optional)", "Name of an environment variable on the server — the password itself is never stored.")}
        </div>
      </div>
      {test && <div className={`banner${test.ok ? "" : " bad"}`} style={{ marginTop: 16 }} role="status">{test.ok ? <CheckCircle2 className="ic" /> : <XCircle className="ic" />}<span>{test.msg}</span></div>}
    </Modal>
  );
}

function DeleteDialog({ src, onClose }: { src: any; onClose: () => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const impact = useQuery({ queryKey: ["impact", src.id], queryFn: () => api<any>(`/api/sources/${src.id}/impact`) });
  const [typed, setTyped] = useState("");
  const del = useMutation({
    mutationFn: () => send("DELETE", `/api/sources/${src.id}`),
    onSuccess: (r: any) => { ["sources", "tree", "stats", "catalog", "facets", "colgroups"].forEach((k) => qc.invalidateQueries({ queryKey: [k] })); toast(`Deleted ${r.deleted} (${r.tables_removed} tables)`); onClose(); },
    onError: (e) => toast(errMsg(e), true),
  });
  const i = impact.data;
  const curated = i ? i.curated_tables + i.curated_columns : 0;
  return (
    <Modal title={`Delete source · ${src.name}`} onClose={onClose}
      footer={<>
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn danger-solid" disabled={typed !== src.name || del.isPending} onClick={() => del.mutate()}>{del.isPending ? "Deleting…" : <><Trash2 className="ic" />Delete source</>}</button>
      </>}>
      {!i ? <p className="muted">Checking what this would remove…</p> : (
        <>
          <p style={{ marginTop: 0 }}>This removes the source from the catalog <b>and everything documented under it</b>. Your data lake is not touched.</p>
          <dl className="kv" style={{ margin: "12px 0" }}>
            <dt>Tables</dt><dd>{i.tables.toLocaleString()} ({i.published_tables} published to agents)</dd>
            <dt>Columns</dt><dd>{i.columns.toLocaleString()}</dd>
            <dt>Hand-written metadata</dt><dd>{i.curated_tables} table and {i.curated_columns} column descriptions</dd>
            <dt>Metrics detached</dt><dd>{i.metrics} (kept, but no longer tied to a table)</dd>
          </dl>
          {curated > 0 && <div className="banner bad"><AlertTriangle className="ic" /><span>Documentation written by your team will be lost. Export columns/tables CSV from the Catalog first if you may want it back.</span></div>}
          <div className="field" style={{ marginTop: 16 }}>
            <label htmlFor="del-confirm">Type <b>{src.name}</b> to confirm</label>
            <input id="del-confirm" value={typed} onChange={(e) => setTyped(e.target.value)} autoFocus />
          </div>
        </>
      )}
    </Modal>
  );
}

function SyncDialog({ src, onClose }: { src: any; onClose: () => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [scope, setScope] = useState("");
  const sync = useMutation({
    mutationFn: () => {
      const qs = scope.split(",").map((x) => x.trim()).filter(Boolean).map((x) => `schema=${encodeURIComponent(x)}`).join("&");
      return send("POST", `/api/sources/${src.id}/sync${qs ? `?${qs}` : ""}`);
    },
    onSuccess: (r: any) => {
      ["sources", "tree", "stats", "catalog", "facets", "colgroups"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
      toast(`Synced ${src.name}: +${r.tables_added} tables, +${r.columns_added} columns, ${r.columns_changed} changed, ${r.tables_removed + r.columns_removed} removed`);
      onClose();
    },
  });
  return (
    <Modal title={`Sync · ${src.name}`} sub="Pull tables and columns from the lake" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn primary" disabled={sync.isPending} onClick={() => sync.mutate()}>{sync.isPending ? <><RefreshCw className="ic spin" />Syncing… (large lakes take a while)</> : <><RefreshCw className="ic" />Sync now</>}</button></>}>
      <p style={{ marginTop: 0 }}>Everything you've written stays. New or changed tables and columns are flagged <span className="chip review">review</span>; anything dropped from the lake is marked, not deleted.</p>
      <div className="field">
        <label htmlFor="sync-scope">Only these schemas (optional)</label>
        <input id="sync-scope" placeholder="blank = every schema, or e.g. sales, finance" value={scope} onChange={(e) => setScope(e.target.value)} />
        <div className="sub" style={{ marginTop: 3 }}>Limiting to some schemas never touches tables in the others.</div>
      </div>
      {sync.isError && <div className="banner bad" style={{ marginTop: 14 }}>{errMsg(sync.error)}</div>}
    </Modal>
  );
}

export default function Sources() {
  useTitle("Sources");
  const { canEdit } = useAuth();
  const sources = useQuery({ queryKey: ["sources"], queryFn: () => api<any[]>("/api/sources") });
  const [dialog, setDialog] = useState<{ kind: "add" | "edit" | "delete" | "sync"; src?: any } | null>(null);
  const close = () => setDialog(null);
  const list = sources.data ?? [];

  return (
    <div className="page">
      <div className="page-head">
        <div><div className="d-kind"><Database className="ic" />Data lake</div><div className="d-title">Sources <InfoTip help={HELP.sources} /></div></div>
        <div className="head-spacer" />
        {canEdit && <button className="btn primary" onClick={() => setDialog({ kind: "add" })}><Plus className="ic" />Add source</button>}
      </div>

      <div className="grid-wrap">
        <table className="grid">
          <thead>
            <tr><th>Source</th><th>Connection</th><th className="num">Tables</th><th className="num">Published</th><th>Last synced</th><th style={{ textAlign: "right" }}>Actions</th></tr>
          </thead>
          <tbody>
            {list.map((s) => (
              <tr key={s.id}>
                <td><b style={{ color: "var(--petrol)" }}>{s.name}</b> <span className="chip">{s.kind}</span></td>
                <td>
                  {s.config.host ? (
                    <>
                      <div style={{ fontFamily: "var(--mono)", fontSize: 12 }}>{s.config.http_scheme ?? "http"}://{s.config.host}{s.config.port ? `:${s.config.port}` : ""}</div>
                      <div className="sub">catalog <b>{s.config.catalog ?? "—"}</b> · user {s.config.user ?? "—"}{s.config.password_env ? ` · $${s.config.password_env}` : ""}</div>
                    </>
                  ) : <span className="chip review">not configured — click Edit</span>}
                </td>
                <td className="num">{s.tables.toLocaleString()}</td>
                <td className="num">{s.published.toLocaleString()}</td>
                <td>{s.last_synced_at ? new Date(s.last_synced_at).toLocaleString() : <span className="chip review with-ic"><AlertTriangle className="ic" />never synced</span>}</td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>{canEdit && <>
                  <button className="btn primary" onClick={() => setDialog({ kind: "sync", src: s })}><RefreshCw className="ic" />Sync</button>{" "}
                  <button className="btn" onClick={() => setDialog({ kind: "edit", src: s })}><Pencil className="ic" />Edit</button>{" "}
                  <button className="btn danger" onClick={() => setDialog({ kind: "delete", src: s })}><Trash2 className="ic" />Delete</button></>}
                </td>
              </tr>
            ))}
            {sources.isLoading && <SkeletonRows rows={3} cols={6} />}
            {sources.isSuccess && !list.length && (
              <tr><td colSpan={6}><EmptyState icon={Database} title="No sources yet" actions={canEdit ? <button className="btn primary" onClick={() => setDialog({ kind: "add" })}><Plus className="ic" />Add source</button> : undefined}>Connect your first data lake to start cataloguing tables and columns.</EmptyState></td></tr>
            )}
          </tbody>
        </table>
      </div>

      {dialog?.kind === "add" && <SourceForm initial={BLANK} onClose={close} />}
      {dialog?.kind === "edit" && <SourceForm initial={toForm(dialog.src)} editing={dialog.src} onClose={close} />}
      {dialog?.kind === "delete" && <DeleteDialog src={dialog.src} onClose={close} />}
      {dialog?.kind === "sync" && <SyncDialog src={dialog.src} onClose={close} />}
    </div>
  );
}
