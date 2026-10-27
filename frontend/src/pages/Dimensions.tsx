import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { AlertTriangle, Link2, Plus, Shapes, Users } from "lucide-react";
import { api, errText, send } from "../api";
import { useAuth } from "../auth";
import { EmptyState, Modal, SearchInput, SkeletonRows, StatusChip, ago, useDebounced, useTitle, useToast, InfoTip } from "../ui";
import { HELP } from "../help";

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").replace(/^(\d)/, "d_$1").slice(0, 63);

function NewDimension({ onClose }: { onClose: () => void }) {
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const [f, setF] = useState({ label: "", label_ar: "", key: "" });
  const [touched, setTouched] = useState(false);
  const key = touched ? f.key : slug(f.label);
  const ok = /^[a-z][a-z0-9_]{1,62}$/.test(key);
  const create = useMutation({
    mutationFn: () => send("POST", "/api/dimensions", { key, label: f.label.trim() || null, label_ar: f.label_ar.trim() || null }),
    onSuccess: (d: any) => { qc.invalidateQueries({ queryKey: ["dimensions"] }); toast("Dimension created"); nav(`/dimensions/${d.id}`); },
    onError: (e) => toast(errText(e), true),
  });
  return (
    <Modal title="New dimension" sub="A business concept answers can be broken down by — independent of any one table" onClose={onClose} width={560}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!ok || create.isPending} onClick={() => create.mutate()}><Plus className="ic" />Create</button></>}>
      <form className="fields" onSubmit={(e) => { e.preventDefault(); ok && create.mutate(); }}>
        <div className="two-col">
          <div className="field"><label htmlFor="nd-l">Label · English</label><input id="nd-l" autoFocus value={f.label} onChange={(e) => setF({ ...f, label: e.target.value })} placeholder="Person category" /></div>
          <div className="field ar"><label htmlFor="nd-la">Label · عربي</label><input id="nd-la" dir="rtl" value={f.label_ar} onChange={(e) => setF({ ...f, label_ar: e.target.value })} placeholder="فئة الشخص" /></div>
        </div>
        <div className="field">
          <label htmlFor="nd-k">Key</label>
          <input id="nd-k" style={{ fontFamily: "var(--mono)" }} value={key} onChange={(e) => { setTouched(true); setF({ ...f, key: e.target.value }); }} placeholder="person_category" />
          <div className="sub" style={{ marginTop: 3 }}>{key && !ok ? "Lowercase letters, digits and underscores; must start with a letter." : "The name rules and tools use for it. It cannot be changed later."}</div>
        </div>
      </form>
    </Modal>
  );
}

export default function Dimensions() {
  useTitle("Dimensions");
  const { canEdit } = useAuth();
  const [q, setQ] = useState("");
  const dq = useDebounced(q);
  const [creating, setCreating] = useState(false);
  const { data, isLoading } = useQuery({ queryKey: ["dimensions", dq], queryFn: () => api<any[]>(`/api/dimensions?q=${encodeURIComponent(dq)}`), placeholderData: (p) => p });

  return (
    <div className="page">
      <div className="page-head">
        <div><div className="d-kind"><Shapes className="ic" />Business vocabulary</div><div className="d-title">Dimensions <InfoTip help={HELP.dimensions} /></div></div>
        <div className="head-spacer" />
        {canEdit && <button className="btn primary" onClick={() => setCreating(true)}><Plus className="ic" />New dimension</button>}
      </div>
      <div className="toolbar"><SearchInput shortcut value={q} onChange={setQ} placeholder="Find a dimension, synonym or value…" label="Find a dimension" /></div>
      <div className="grid-wrap">
        <table className="grid">
          <thead><tr><th>Dimension</th><th>Status</th><th className="num">Values</th><th className="num">Columns</th><th>Applies to</th><th>Checks</th><th>Updated</th></tr></thead>
          <tbody>
            {data?.map((d) => (
              <tr key={d.id}>
                <td>
                  <Link className="tname" to={`/dimensions/${d.id}`}><Shapes className="t-ic" />{d.label || d.key}</Link>
                  {d.label_ar && <span className="ar-text" dir="rtl" style={{ marginLeft: 8, color: "var(--ink-2)" }}>{d.label_ar}</span>}
                  <div className="sub" style={{ fontFamily: "var(--mono)" }}>{d.key}</div>
                </td>
                <td>
                  <StatusChip status={d.status} />
                  {d.draft_id && <Link className="chip info" style={{ marginInlineStart: 6 }} to={`/dimensions/${d.draft_id}`}>edit {d.draft_status}</Link>}
                </td>
                <td className="num">{d.values}{d.families > 0 && <span className="sub"> · {d.families} {d.families === 1 ? "family" : "families"}</span>}</td>
                <td className="num">{d.bindings || <span className="muted">—</span>}</td>
                <td>{d.applies ? <span className="chip gold-soft with-ic"><Users className="ic" />restricted</span> : <span className="muted">everyone</span>}</td>
                <td>
                  {d.errors > 0 ? <span className="chip hold with-ic"><AlertTriangle className="ic" />{d.errors} error{d.errors === 1 ? "" : "s"}</span>
                    : d.warnings > 0 ? <span className="chip gold-soft with-ic"><AlertTriangle className="ic" />{d.warnings} warning{d.warnings === 1 ? "" : "s"}</span>
                    : <span className="muted">ok</span>}
                </td>
                <td className="sub">{ago(d.updated_at)}</td>
              </tr>
            ))}
            {isLoading && <SkeletonRows rows={4} cols={7} />}
            {data && !data.length && (
              <tr><td colSpan={7}>
                <EmptyState icon={Link2} title={dq ? "No dimension matches" : "No dimensions yet"} actions={!dq && canEdit ? <button className="btn primary" onClick={() => setCreating(true)}><Plus className="ic" />New dimension</button> : undefined}>
                  {dq ? "Try another word." : "Create one for each way your data is broken down, then link it to the columns that hold it."}
                </EmptyState>
              </td></tr>
            )}
          </tbody>
        </table>
      </div>
      {creating && <NewDimension onClose={() => setCreating(false)} />}
    </div>
  );
}
