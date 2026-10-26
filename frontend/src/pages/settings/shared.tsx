import { ReactNode, useState } from "react";
import { AlertTriangle } from "lucide-react";
import { CopyButton, Modal } from "../../ui";

export function Confirm({ title, children, confirmLabel, danger, busy, onConfirm, onClose }: { title: string; children: ReactNode; confirmLabel: string; danger?: boolean; busy?: boolean; onConfirm: () => void; onClose: () => void }) {
  return (
    <Modal title={title} onClose={onClose} width={520}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className={`btn ${danger ? "danger-solid" : "primary"}`} disabled={busy} onClick={onConfirm}>{busy ? "Working…" : confirmLabel}</button></>}>
      <div style={{ color: "var(--ink-2)" }}>{children}</div>
    </Modal>
  );
}

export function Snippet({ title, code }: { title: string; code: string }) {
  return (
    <div className="snip">
      <div className="snip-head"><span>{title}</span><CopyButton text={code} /></div>
      <pre>{code}</pre>
    </div>
  );
}

/** A secret that is displayed exactly once. */
export function SecretReveal({ title, secret, hint, children, onClose }: { title: string; secret: string; hint: string; children?: ReactNode; onClose: () => void }) {
  const [saved, setSaved] = useState(false);
  return (
    <Modal title={title} onClose={() => saved && onClose()} width={700}
      footer={<button className="btn primary" disabled={!saved} onClick={onClose}>Done</button>}>
      <div className="banner" style={{ margin: "0 0 14px" }}><AlertTriangle className="ic" /><span>{hint}</span></div>
      <div className="secret"><code>{secret}</code><CopyButton text={secret} /></div>
      <label className="check-inline" style={{ margin: "14px 0" }}><input type="checkbox" checked={saved} onChange={(e) => setSaved(e.target.checked)} /> I have copied it and stored it somewhere safe</label>
      {children}
    </Modal>
  );
}

export const csvList = (v: string) => v.split(",").map((s) => s.trim()).filter(Boolean);
