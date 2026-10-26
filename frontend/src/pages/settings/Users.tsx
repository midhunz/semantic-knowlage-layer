import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, errText, send } from "../../api";
import { useAuth } from "../../auth";
import { KeyRound, Pencil, Plus, RotateCw, ShieldAlert, Trash2, UserCheck, UserPlus, UserX, Users as UsersIcon } from "lucide-react";
import { Avatar, CopyButton, EmptyState, Modal, ROLE_BADGE, SkeletonRows, ago } from "../../ui";
import { useToast } from "../../ui";
import { Confirm } from "./shared";

const ROLE_LABEL: Record<string, string> = { admin: "Administrator", steward: "Steward", viewer: "Viewer" };

function AddUser({ onClose, onCreated }: { onClose: () => void; onCreated: (r: any) => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const meta = useQuery({ queryKey: ["admin-meta"], queryFn: () => api<any>("/api/admin/meta") });
  const [f, setF] = useState({ name: "", email: "", role: "steward", password: "" });
  const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f.email);
  const save = useMutation({
    mutationFn: () => send("POST", "/api/admin/users", { ...f, password: f.password || null }),
    onSuccess: (r) => { qc.invalidateQueries({ queryKey: ["users"] }); onCreated(r); },
    onError: (e) => toast(errText(e), true),
  });
  return (
    <Modal title="Add a user" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!emailOk || save.isPending || (!!f.password && f.password.length < 8)} onClick={() => save.mutate()}>Add user</button></>}>
      <div className="fields">
        <div className="two-col">
          <div className="field"><label htmlFor="un">Name</label><input id="un" autoFocus value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></div>
          <div className="field"><label htmlFor="ue">Email</label><input id="ue" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
        </div>
        <div className="field"><label>Role</label>
          <div className="radio-cards" role="radiogroup">
            {meta.data?.roles.map((r: any) => (
              <div key={r.id} role="radio" aria-checked={f.role === r.id} tabIndex={0} className={`rcard${f.role === r.id ? " sel" : ""}`} onClick={() => setF({ ...f, role: r.id })} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), setF({ ...f, role: r.id }))}>
                <div className="radio" /><div><b style={{ display: "flex", alignItems: "center", gap: 6 }}>{(() => { const I = ROLE_BADGE[r.id]; return I ? <I className="ic" /> : null; })()}{ROLE_LABEL[r.id]}</b><span>{r.description}</span></div>
              </div>
            ))}
          </div>
        </div>
        <div className="field"><label htmlFor="up">Password (optional)</label>
          <input id="up" type="text" autoComplete="off" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} placeholder="Leave blank to generate a temporary one" />
          <div className="sub" style={{ marginTop: 3 }}>With a temporary password, the person is asked to choose their own at first sign-in.</div></div>
      </div>
    </Modal>
  );
}

export default function Users() {
  const qc = useQueryClient();
  const toast = useToast();
  const { me } = useAuth();
  const { data, isLoading } = useQuery({ queryKey: ["users"], queryFn: () => api<any[]>("/api/admin/users"), enabled: !me.setup_needed });
  const [dlg, setDlg] = useState<{ kind: "add" | "reset" | "delete"; user?: any } | null>(null);
  const [temp, setTemp] = useState<{ email: string; password: string } | null>(null);
  const refresh = () => qc.invalidateQueries({ queryKey: ["users"] });
  const patch = useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) => send("PATCH", `/api/admin/users/${id}`, body),
    onSuccess: refresh, onError: (e) => { toast(errText(e), true); refresh(); },
  });
  const act = useMutation({
    mutationFn: ({ kind, id }: { kind: string; id: number }) => (kind === "delete" ? send("DELETE", `/api/admin/users/${id}`) : send("POST", `/api/admin/users/${id}/reset-password`)),
    onSuccess: (r: any, v) => { refresh(); setDlg(null); if (v.kind === "reset") setTemp({ email: r.user.email, password: r.temporary_password }); else toast("User deleted"); },
    onError: (e) => toast(errText(e), true),
  });

  if (me.setup_needed) {
    return <section className="card"><h3><UsersIcon className="ic" />Users</h3><div className="banner" style={{ margin: "10px 0 0" }}><ShieldAlert className="ic" /><span>No accounts exist yet, so everyone with access to this address can edit the catalog. Use <b>Secure this catalog</b> in the yellow bar at the top to create the first administrator — then you can add people here.</span></div></section>;
  }
  const list = data ?? [];
  return (
    <>
      <section className="card">
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
          <div style={{ flex: 1 }}>
            <h3><UsersIcon className="ic" />Users</h3>
            <p className="hint" style={{ marginBottom: 0 }}>People who can sign in. <b>Viewers</b> browse, <b>stewards</b> document and publish, <b>administrators</b> also manage settings, users, keys and webhooks.</p>
          </div>
          <button className="btn primary" onClick={() => setDlg({ kind: "add" })}><UserPlus className="ic" />Add user</button>
        </div>
        <div className="grid-wrap" style={{ marginTop: 14 }}>
          <table className="grid">
            <thead><tr><th>User</th><th>Role</th><th>Status</th><th>Last sign-in</th><th style={{ textAlign: "right" }}>Actions</th></tr></thead>
            <tbody>
              {list.map((u) => {
                const self = u.id === me.user?.id;
                return (
                  <tr key={u.id} style={!u.is_active ? { opacity: 0.6 } : undefined}>
                    <td><div style={{ display: "flex", alignItems: "center", gap: 10 }}><Avatar name={u.name || u.email} size={32} /><div><b style={{ color: "var(--petrol)" }}>{u.name || u.email}</b>{self && <span className="chip gold" style={{ marginInlineStart: 8 }}>you</span>}{u.name && <div className="sub">{u.email}</div>}</div></div></td>
                    <td>
                      <select aria-label={`Role of ${u.email}`} value={u.role} onChange={(e) => patch.mutate({ id: u.id, body: { role: e.target.value } })} style={{ font: "inherit", fontSize: 13, padding: "4px 6px", border: "1px solid var(--line)", borderRadius: 6 }}>
                        {Object.entries(ROLE_LABEL).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                      </select>
                    </td>
                    <td><span className={`chip ${u.is_active ? "ok" : "warn"}`}>{u.is_active ? "active" : "deactivated"}</span>{u.must_change_password && <div className="sub">temporary password</div>}</td>
                    <td>{u.last_login_at ? ago(u.last_login_at) : <span className="muted">never</span>}</td>
                    <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                      <button className="btn" onClick={() => setDlg({ kind: "reset", user: u })}><KeyRound className="ic" />Reset password</button>{" "}
                      {!self && <button className="btn" onClick={() => patch.mutate({ id: u.id, body: { is_active: !u.is_active } })}>{u.is_active ? <><UserX className="ic" />Deactivate</> : <><UserCheck className="ic" />Reactivate</>}</button>}{" "}
                      {!self && <button className="btn danger" onClick={() => setDlg({ kind: "delete", user: u })}><Trash2 className="ic" />Delete</button>}
                    </td>
                  </tr>
                );
              })}
              {isLoading && <SkeletonRows rows={3} cols={5} />}
              {!isLoading && !list.length && <tr><td colSpan={5}><EmptyState icon={UsersIcon} title="No users" /></td></tr>}
            </tbody>
          </table>
        </div>
      </section>

      {dlg?.kind === "add" && <AddUser onClose={() => setDlg(null)} onCreated={(r) => { setDlg(null); if (r.temporary_password) setTemp({ email: r.user.email, password: r.temporary_password }); else toast("User added"); }} />}
      {dlg?.kind === "reset" && <Confirm title={`Reset password for ${dlg.user.email}?`} confirmLabel="Reset and show temporary password" busy={act.isPending} onClose={() => setDlg(null)} onConfirm={() => act.mutate({ kind: "reset", id: dlg.user.id })}>They are signed out everywhere and must choose a new password at next sign-in.</Confirm>}
      {dlg?.kind === "delete" && <Confirm title={`Delete ${dlg.user.email}?`} danger confirmLabel="Delete user" busy={act.isPending} onClose={() => setDlg(null)} onConfirm={() => act.mutate({ kind: "delete", id: dlg.user.id })}>Their account is removed. Their past edits stay in the audit log. To keep the account but block sign-in, use <b>Deactivate</b> instead.</Confirm>}
      {temp && (
        <Modal title="Temporary password" onClose={() => setTemp(null)} width={520} footer={<button className="btn primary" onClick={() => setTemp(null)}>Done</button>}>
          <p style={{ marginTop: 0 }}>Share this with <b>{temp.email}</b> through a secure channel. It is shown only now.</p>
          <div className="secret"><code>{temp.password}</code><CopyButton text={temp.password} /></div>
        </Modal>
      )}
    </>
  );
}
