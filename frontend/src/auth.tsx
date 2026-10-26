import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Lock, LogIn } from "lucide-react";
import { api, errText, send } from "./api";

export type Me = {
  auth_required: boolean; setup_needed: boolean; needs_cli_setup?: boolean; org_name: string;
  user: null | { id: number; email: string; name: string; role: "admin" | "steward" | "viewer"; must_change_password: boolean };
};
type Ctx = { me: Me; isAdmin: boolean; canEdit: boolean; refresh: () => void };
const AuthCtx = createContext<Ctx>({ me: { auth_required: false, setup_needed: true, org_name: "", user: null }, isAdmin: true, canEdit: true, refresh: () => {} });
export const useAuth = () => useContext(AuthCtx);

function Shell({ title, sub, children }: { title: string; sub?: string; children: ReactNode }) {
  return (
    <div className="login-wrap">
      <div className="login-card">
        <img className="logo" src="/vendor/icp-logo.png" alt="ICP" style={{ height: 40 }} />
        <div className="lock"><Lock /></div>
        <h1>{title}</h1>
        {sub && <p className="muted">{sub}</p>}
        {children}
      </div>
    </div>
  );
}

function Login({ orgName, needsCli, onDone }: { orgName: string; needsCli?: boolean; onDone: () => void }) {
  const [f, setF] = useState({ email: "", password: "" });
  const m = useMutation({ mutationFn: () => send("POST", "/api/auth/login", f), onSuccess: onDone });
  return (
    <Shell title="Sign in" sub={orgName ? `${orgName} · Semantic Layer` : "Semantic Layer"}>
      <form onSubmit={(e) => { e.preventDefault(); m.mutate(); }} className="fields">
        <div className="field"><label htmlFor="em">Email</label><input id="em" type="email" autoComplete="username" autoFocus value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
        <div className="field"><label htmlFor="pw">Password</label><input id="pw" type="password" autoComplete="current-password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></div>
        {needsCli && (
          <div className="banner" role="status" style={{ margin: 0, textAlign: "start" }}>
            <span>No administrator exists yet. On the server, run <code>python -m app.cli create-admin --email you@example.com</code>, then sign in here.</span>
          </div>
        )}
        {m.isError && <div className="banner bad" role="alert" style={{ margin: 0 }}>{errText(m.error)}</div>}
        <button className="btn primary" style={{ justifyContent: "center", padding: "10px" }} disabled={!f.email || !f.password || m.isPending}>{m.isPending ? "Signing in…" : <><LogIn className="ic" />Sign in</>}</button>
      </form>
    </Shell>
  );
}

/** Create the first administrator. Shown from the open-mode banner. */
export function SetupDialog({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [f, setF] = useState({ name: "", email: "", password: "" });
  const m = useMutation({ mutationFn: () => send("POST", "/api/auth/setup", f), onSuccess: onDone });
  const ok = f.email.includes("@") && f.password.length >= 8;
  return (
    <div className="modal open" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="sheet" style={{ width: "min(480px,100%)" }}>
        <div className="sheet-head"><div><h2 className="sheet-title">Create the administrator</h2><div className="sheet-sub">After this, signing in is required for everyone.</div></div><div className="spacer" /><button className="btn ghost" onClick={onClose}>✕</button></div>
        <form className="fields" style={{ padding: 20 }} onSubmit={(e) => { e.preventDefault(); ok && m.mutate(); }}>
          <div className="field"><label htmlFor="su-name">Your name</label><input id="su-name" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} autoFocus /></div>
          <div className="field"><label htmlFor="su-email">Email</label><input id="su-email" type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></div>
          <div className="field"><label htmlFor="su-pw">Password</label><input id="su-pw" type="password" autoComplete="new-password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /><div className="sub" style={{ marginTop: 3 }}>At least 8 characters.</div></div>
          {m.isError && <div className="banner bad" style={{ margin: 0 }}>{errText(m.error)}</div>}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}><button type="button" className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!ok || m.isPending}>Create administrator</button></div>
        </form>
      </div>
    </div>
  );
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const { data: me, isLoading, refetch, isError } = useQuery({ queryKey: ["me"], queryFn: () => api<Me>("/api/auth/me"), retry: false });
  useEffect(() => {
    const h = () => refetch();
    window.addEventListener("sl:unauthorized", h);
    return () => window.removeEventListener("sl:unauthorized", h);
  }, [refetch]);

  if (isLoading) return <div className="loading" style={{ paddingTop: 120 }}>Loading…</div>;
  if (isError || !me) return <div className="loading" style={{ paddingTop: 120 }}>Cannot reach the server. Is the API running?</div>;
  const refresh = () => { qc.clear(); refetch(); };
  if (me.auth_required && !me.user) return <Login orgName={me.org_name} needsCli={me.needs_cli_setup} onDone={refresh} />;

  const role = me.user?.role;
  const value: Ctx = {
    me, refresh,
    isAdmin: !me.auth_required || role === "admin",
    canEdit: !me.auth_required || role === "admin" || role === "steward",
  };
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export function ChangePasswordDialog({ onClose, forced }: { onClose: () => void; forced?: boolean }) {
  const [f, setF] = useState({ current: "", new: "" });
  const [done, setDone] = useState(false);
  const { refresh } = useAuth();
  const m = useMutation({ mutationFn: () => send("POST", "/api/auth/change-password", f), onSuccess: () => { setDone(true); setTimeout(() => { onClose(); refresh(); }, 900); } });
  return (
    <div className="modal open" onMouseDown={(e) => !forced && e.target === e.currentTarget && onClose()}>
      <div className="sheet" style={{ width: "min(460px,100%)" }}>
        <div className="sheet-head"><div><h2 className="sheet-title">{forced ? "Choose a new password" : "Change password"}</h2>{forced && <div className="sheet-sub">You are using a temporary password.</div>}</div><div className="spacer" />{!forced && <button className="btn ghost" onClick={onClose}>✕</button>}</div>
        <form className="fields" style={{ padding: 20 }} onSubmit={(e) => { e.preventDefault(); m.mutate(); }}>
          <div className="field"><label htmlFor="cp-cur">{forced ? "Temporary password" : "Current password"}</label><input id="cp-cur" type="password" autoComplete="current-password" value={f.current} onChange={(e) => setF({ ...f, current: e.target.value })} autoFocus /></div>
          <div className="field"><label htmlFor="cp-new">New password</label><input id="cp-new" type="password" autoComplete="new-password" value={f.new} onChange={(e) => setF({ ...f, new: e.target.value })} /><div className="sub" style={{ marginTop: 3 }}>At least 8 characters.</div></div>
          {m.isError && <div className="banner bad" style={{ margin: 0 }}>{errText(m.error)}</div>}
          {done && <div className="banner" style={{ margin: 0 }}>✓ Password changed</div>}
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>{!forced && <button type="button" className="btn" onClick={onClose}>Cancel</button>}<button className="btn primary" disabled={!f.current || f.new.length < 8 || m.isPending}>Change password</button></div>
        </form>
      </div>
    </div>
  );
}
