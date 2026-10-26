import { Component, createContext, useContext, useEffect, useId, useLayoutEffect, useRef, useState, ReactNode } from "react";
import { useIsMutating } from "@tanstack/react-query";
import { RefreshCw, AlertTriangle, Languages, AlertCircle, Check, CheckCheck, CheckCircle2, ChevronDown, ChevronLeft, ChevronRight, CircleDashed, Copy, Hash, Key, Layers, Loader2, LucideIcon, Search, Shield, ShieldCheck, Tag, Clock, Eye, Info, X } from "lucide-react";
import { useAuth } from "./auth";

/* ---------------------------------------------------------------- language mode */
export type Lang = "en" | "ar" | "both";
const LangCtx = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({ lang: "both", setLang: () => {} });
export const useLang = () => useContext(LangCtx);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    try { return (localStorage.getItem("sl.lang") as Lang) || "both"; } catch { return "both"; }
  });
  const setLang = (l: Lang) => { setLangState(l); try { localStorage.setItem("sl.lang", l); } catch { /* ignore */ } };
  return <LangCtx.Provider value={{ lang, setLang }}>{children}</LangCtx.Provider>;
}

export function LangToggle() {
  const { lang, setLang } = useLang();
  return (
    <div className="seg" title="Which language to edit"><span className="seg-ic"><Languages className="ic" /></span>
      {(["en", "both", "ar"] as Lang[]).map((l) => (
        <button key={l} className={lang === l ? "on" : ""} onClick={() => setLang(l)}>{l === "en" ? "EN" : l === "ar" ? "عربي" : "EN + عربي"}</button>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- toast */
const ToastCtx = createContext<(msg: string, bad?: boolean) => void>(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [t, setT] = useState<{ msg: string; bad: boolean } | null>(null);
  useEffect(() => { if (t) { const id = setTimeout(() => setT(null), 3800); return () => clearTimeout(id); } }, [t]);
  useEffect(() => {
    const h = (e: Event) => setT({ msg: (e as CustomEvent).detail || "Your access is read-only", bad: true });
    window.addEventListener("sl:forbidden", h);
    return () => window.removeEventListener("sl:forbidden", h);
  }, []);
  return (
    <ToastCtx.Provider value={(msg, bad = false) => setT({ msg, bad })}>
      {children}
      <div className={`toast${t ? " show" : ""}${t?.bad ? " bad" : ""}`} role="status" aria-live="polite">
        {t && (t.bad ? <AlertCircle className="ic" /> : <CheckCircle2 className="ic" />)}<span>{t?.msg}</span>
      </div>
    </ToastCtx.Provider>
  );
}

/* ---------------------------------------------------------------- fields */
export const csv = (v: string) => v.split(/[,،]/).map((s) => s.trim()).filter(Boolean);

type TextProps = { label: string; staged?: boolean; badge?: string; value: string; onSave: (v: string) => void; area?: boolean; rtl?: boolean; placeholder?: string };

export function Text({ label, staged, badge, value, onSave, area, rtl, placeholder }: TextProps) {
  const { canEdit } = useAuth();
  const id = useId();
  const [v, setV] = useState(value);
  useEffect(() => setV(value), [value]);
  const props = {
    id, value: v, placeholder, readOnly: !canEdit, onChange: (e: any) => setV(e.target.value),
    onBlur: () => v !== value && onSave(v),
    ...(rtl ? { dir: "rtl" as const, lang: "ar" } : { dir: "auto" as const }),
  };
  return (
    <div className={`field${rtl ? " ar" : ""}${staged ? " staged" : ""}`}>
      <label htmlFor={id}>{label}{badge && <span className={`lg${rtl ? " ar" : ""}`}>{badge}</span>}{staged && <span className="unpub" title="Saved as a pending change; agents do not see it until it is published">unpublished</span>}</label>
      {area ? <textarea {...props} /> : <input {...props} />}
    </div>
  );
}

/** One field, two languages. Shows EN, AR or side-by-side depending on the language toggle. */
export function Bi({ label, en, ar, onEn, onAr, area, stagedEn, stagedAr }: { label: string; en: string; ar: string; onEn: (v: string) => void; onAr: (v: string) => void; area?: boolean; stagedEn?: boolean; stagedAr?: boolean }) {
  const { lang } = useLang();
  const e = <Text key="en" label={label} staged={stagedEn} badge={lang === "both" ? "EN" : undefined} value={en} onSave={onEn} area={area} />;
  const a = <Text key="ar" label={label} staged={stagedAr} badge={lang === "both" ? "عربي" : undefined} value={ar} onSave={onAr} area={area} rtl />;
  if (lang === "en") return e;
  if (lang === "ar") return en && !ar ? <div>{a}<p className="fallback-hint" lang="en" dir="auto"><b>English:</b> {en.length > 220 ? `${en.slice(0, 220)}…` : en}</p></div> : a;
  return <div className="two-col">{e}{a}</div>;
}

export function Select({ label, value, options, onSave, staged }: { label: string; value: string; options: string[]; onSave: (v: string) => void; staged?: boolean }) {
  const { canEdit } = useAuth();
  const id = useId();
  return (
    <div className={`field${staged ? " staged" : ""}`}>
      <label htmlFor={id}>{label}{staged && <span className="unpub">unpublished</span>}</label>
      <select id={id} value={value} disabled={!canEdit} onChange={(e) => onSave(e.target.value)}>{options.map((o) => <option key={o} value={o}>{o || "—"}</option>)}</select>
    </div>
  );
}

/* ---------------------------------------------------------------- coverage */
export const pct = (x: number) => `${Math.round(x * 100)}%`;

export function Cov({ en, ar, wide }: { en: number; ar?: number; wide?: boolean }) {
  return (
    <div className={`cov${wide ? " wide" : ""}`}>
      <div className="cov-row"><span>EN</span><div className="meter"><i style={{ width: pct(en) }} /></div><b>{pct(en)}</b></div>
      {ar !== undefined && <div className="cov-row"><span>AR</span><div className="meter ar"><i style={{ width: pct(ar) }} /></div><b>{pct(ar)}</b></div>}
    </div>
  );
}

export function Pager({ page, pageSize, total, onPage }: { page: number; pageSize: number; total: number; onPage: (p: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const from = total ? (page - 1) * pageSize + 1 : 0;
  return (
    <div className="pager">
      <span className="muted">{from}–{Math.min(page * pageSize, total)} of {total.toLocaleString()}</span>
      <button className="btn" disabled={page <= 1} onClick={() => onPage(page - 1)}><ChevronLeft className="ic" />Prev</button>
      <span>{page} / {pages}</span>
      <button className="btn" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next<ChevronRight className="ic" /></button>
    </div>
  );
}

export function useDebounced<T>(value: T, ms = 250) {
  const [v, setV] = useState(value);
  useEffect(() => { const id = setTimeout(() => setV(value), ms); return () => clearTimeout(id); }, [value, ms]);
  return v;
}

/** "Saving… / All changes saved" — edits save on blur, so say so. */
export function SaveIndicator() {
  const busy = useIsMutating() > 0;
  const [saved, setSaved] = useState(false);
  const was = useRef(false);
  useEffect(() => {
    if (was.current && !busy) { setSaved(true); const id = setTimeout(() => setSaved(false), 2500); return () => clearTimeout(id); }
    was.current = busy;
  }, [busy]);
  useEffect(() => { was.current = busy; }, [busy]);
  return (
    <span className={`saving${busy ? " busy" : ""}`} aria-live="polite">
      {busy ? <><Loader2 className="ic spin" />Saving…</> : saved ? <><Check className="ic" />Saved</> : null}
    </span>
  );
}

/** Dropdown menu built on <details>; closes after an item is chosen. */
export function Menu({ label, className = "", children }: { label: ReactNode; className?: string; children: (close: () => void) => ReactNode }) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) ref.current.open = false; };
    const k = (e: KeyboardEvent) => {
      if (e.key === "Escape" && ref.current?.open) { ref.current.open = false; ref.current.querySelector("summary")?.focus(); }
    };
    document.addEventListener("mousedown", h);
    document.addEventListener("keydown", k);
    return () => { document.removeEventListener("mousedown", h); document.removeEventListener("keydown", k); };
  }, []);
  return (
    <details className="menu" ref={ref}>
      <summary className={`btn ${className}`}>{label}<ChevronDown className="ic" /></summary>
      <div className="items">{children(() => { if (ref.current) ref.current.open = false; })}</div>
    </details>
  );
}

/* ---------------------------------------------------------------- dialogs & helpers */
export function Modal({ title, sub, onClose, children, footer, width = 640 }: { title: string; sub?: string; onClose: () => void; children: ReactNode; footer?: ReactNode; width?: number }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="modal open" onMouseDown={(e) => e.target === e.currentTarget && onClose()} role="dialog" aria-modal="true" aria-label={title}>
      <div className="sheet" style={{ width: `min(${width}px,100%)` }}>
        <div className="sheet-head">
          <div><h2 className="sheet-title">{title}</h2>{sub && <div className="sheet-sub">{sub}</div>}</div>
          <div className="spacer" />
          <button className="btn ghost icon-only" onClick={onClose} aria-label="Close"><X className="ic" /></button>
        </div>
        <div style={{ padding: 20, overflowY: "auto" }}>{children}</div>
        {footer && <div className="sheet-head" style={{ borderTop: "1px solid var(--line)", borderBottom: 0, justifyContent: "flex-end" }}>{footer}</div>}
      </div>
    </div>
  );
}

export function CopyButton({ text, label = "Copy" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button className="btn" onClick={async () => {
      try { await navigator.clipboard.writeText(text); } catch {
        const ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove();
      }
      setDone(true); setTimeout(() => setDone(false), 1800);
    }}>{done ? <><Check className="ic" />Copied</> : <><Copy className="ic" />{label}</>}</button>
  );
}

/** Server timestamps are UTC without a zone suffix. */
export const parseDate = (s?: string | null) => (s ? new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? s : s + "Z") : null);
export function ago(s?: string | null): string {
  const d = parseDate(s);
  if (!d) return "never";
  const sec = Math.round((Date.now() - d.getTime()) / 1000);
  if (sec < 60) return "just now";
  const units: [number, string][] = [[60, "minute"], [3600, "hour"], [86400, "day"], [2592000, "month"]];
  let best: [number, string] = [1, "second"];
  for (const u of units) if (sec >= u[0]) best = u;
  const n = Math.floor(sec / best[0]);
  return n >= 12 && best[1] === "month" ? `${Math.floor(n / 12)}y ago` : `${n} ${best[1]}${n === 1 ? "" : "s"} ago`;
}
export const when = (s?: string | null) => parseDate(s)?.toLocaleString() ?? "—";

export function Switch({ checked, onChange, label, hint, disabled }: { checked: boolean; onChange: (v: boolean) => void; label: string; hint?: string; disabled?: boolean }) {
  return (
    <label className="switch-row">
      <span className="switch"><input type="checkbox" role="switch" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)} /><i /></span>
      <span><b>{label}</b>{hint && <span className="sub" style={{ display: "block" }}>{hint}</span>}</span>
    </label>
  );
}

/* ---------------------------------------------------------------- polish: search, empty states, skeletons, avatars, chips */
export function SearchInput({ value, onChange, placeholder, label, width, shortcut }: { value: string; onChange: (v: string) => void; placeholder: string; label?: string; width?: number | string; shortcut?: boolean }) {
  return (
    <div className="search" style={width ? { width } : undefined}>
      <Search className="ic" />
      <input type="search" aria-label={label ?? placeholder} placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} data-searchbox={shortcut ? "" : undefined} />
      {shortcut && !value && <kbd aria-hidden>/</kbd>}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, children, actions }: { icon: LucideIcon; title: string; children?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="empty-state">
      <div className="es-icon"><Icon /></div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {actions && <div className="es-actions">{actions}</div>}
    </div>
  );
}

/** Placeholder rows while a table loads — keeps the layout from jumping. */
export function SkeletonRows({ rows = 8, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }, (_, r) => (
        <tr key={r} className="skeleton-row" aria-hidden>
          {Array.from({ length: cols }, (_, c) => <td key={c}><i style={{ width: `${c === 0 ? 70 : 40 + ((r * 7 + c * 13) % 40)}%` }} /></td>)}
        </tr>
      ))}
    </>
  );
}

export function useTitle(title: string) {
  useEffect(() => { document.title = `${title} · Semantic Layer`; }, [title]);
}

const AVATAR_HUES = [196, 170, 38, 12, 262, 210, 340, 95];
export function Avatar({ name, size = 28 }: { name: string; size?: number }) {
  const parts = name.replace(/@.*/, "").split(/[\s._-]+/).filter(Boolean);
  const initials = ((parts[0]?.[0] ?? "?") + (parts[1]?.[0] ?? "")).toUpperCase();
  const hue = AVATAR_HUES[[...name].reduce((a, c) => a + c.charCodeAt(0), 0) % AVATAR_HUES.length];
  return <span className="avatar" aria-hidden style={{ width: size, height: size, fontSize: Math.max(12, size * 0.4), background: `hsl(${hue} 45% 92%)`, color: `hsl(${hue} 55% 26%)` }}>{initials}</span>;
}

export const ROLE_ICON: Record<string, LucideIcon> = { identifier: Key, measure: Hash, dimension: Layers, time: Clock, attribute: Tag };
export function RoleChip({ role }: { role: string }) {
  const Icon = ROLE_ICON[role];
  return <span className="chip with-ic">{Icon && <Icon className="ic" />}{role}</span>;
}

const STATUS: Record<string, { icon: LucideIcon; cls: string }> = {
  published: { icon: CheckCircle2, cls: "ok" },
  reviewed: { icon: CheckCheck, cls: "info" },
  draft: { icon: CircleDashed, cls: "" },
};
export function StatusChip({ status }: { status: string }) {
  const m = STATUS[status] ?? STATUS.draft;
  return <span className={`chip with-ic ${m.cls}`}><m.icon className="ic" />{status}</span>;
}

export const ROLE_BADGE: Record<string, LucideIcon> = { admin: ShieldCheck, steward: Shield, viewer: Eye };

/** Catches render errors so one bad screen never turns the whole app white. */
export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error) { console.error(error); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ paddingTop: 60 }}>
        <EmptyState icon={AlertTriangle} title="Something went wrong on this page"
          actions={<><button className="btn primary" onClick={() => window.location.reload()}><RefreshCw className="ic" />Reload</button><button className="btn" onClick={() => { this.setState({ error: null }); }}>Try again</button></>}>
          {this.state.error.message || "An unexpected error occurred."} Your changes are saved as you type, so nothing is lost.
        </EmptyState>
      </div>
    );
  }
}

/* ---------------------------------------------------------------- tags (words people say) */
export const hasArabic = (s: string) => /[؀-ۿݐ-ݿ]/.test(s);

/** A list of short words, added with Enter or a comma, removed with × — used for aliases. */
export function Tags({ value, onChange, placeholder, disabled, label }: { value: string[]; onChange: (v: string[]) => void; placeholder?: string; disabled?: boolean; label?: string }) {
  const [draft, setDraft] = useState("");
  const add = (raw: string) => {
    const words = raw.split(/[,\n;،]/).map((s) => s.trim()).filter(Boolean);
    if (!words.length) return setDraft("");
    const next = [...value];
    for (const w of words) if (!next.some((x) => x.toLowerCase() === w.toLowerCase())) next.push(w);
    setDraft("");
    if (next.length !== value.length) onChange(next);
  };
  return (
    <div className={`tags${disabled ? " ro" : ""}`} role="group" aria-label={label}>
      {value.map((w) => (
        <span key={w} className={`tag${hasArabic(w) ? " ar" : ""}`} dir="auto">
          {w}
          {!disabled && <button type="button" aria-label={`Remove ${w}`} onClick={() => onChange(value.filter((x) => x !== w))}>×</button>}
        </span>
      ))}
      {!disabled && (
        <input value={draft} placeholder={value.length ? "" : placeholder} aria-label={label ?? "Add a word"} dir="auto"
          onChange={(e) => (/[,،;]$/.test(e.target.value) ? add(e.target.value) : setDraft(e.target.value))}
          onKeyDown={(e) => {
            if (e.key === "Enter") { e.preventDefault(); add(draft); }
            else if (e.key === "Backspace" && !draft && value.length) onChange(value.slice(0, -1));
          }}
          onBlur={() => add(draft)} />
      )}
    </div>
  );
}

/** Pick some of a list of values by toggling chips. */
export function ValueChips({ options, value, onChange, disabled }: { options: string[]; value: string[]; onChange: (v: string[]) => void; disabled?: boolean }) {
  if (!options.length) return <span className="muted">No values listed yet.</span>;
  return (
    <div className="chips" style={{ margin: 0 }}>
      {options.map((o) => (
        <button type="button" key={o} disabled={disabled} className={`pill${value.includes(o) ? " on" : ""}`} aria-pressed={value.includes(o)}
          onClick={() => onChange(value.includes(o) ? value.filter((x) => x !== o) : [...value, o])}>{o}</button>
      ))}
    </div>
  );
}


/* ---------------------------------------------------------------- page help */
export type HelpContent = { title: string; lead: ReactNode; points?: ReactNode[]; note?: ReactNode };

/**
 * The "i" next to a page title. Opens on hover or keyboard focus, pins open on click/tap, and closes on
 * Escape, outside click or scroll. The panel is fixed-positioned so no scroll container can clip it.
 */
export function InfoTip({ help }: { help: HelpContent }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number; width: number } | null>(null);
  const wrap = useRef<HTMLSpanElement>(null);
  const btn = useRef<HTMLButtonElement>(null);
  const timer = useRef<number>();
  const pin = useRef(false);
  pin.current = pinned;
  const show = (ms = 120) => { window.clearTimeout(timer.current); timer.current = window.setTimeout(() => setOpen(true), ms); };
  const hide = (ms = 220) => { window.clearTimeout(timer.current); timer.current = window.setTimeout(() => { if (!pin.current) setOpen(false); }, ms); };
  useEffect(() => () => window.clearTimeout(timer.current), []);

  useLayoutEffect(() => {
    if (!open || !btn.current) return;
    const r = btn.current.getBoundingClientRect();
    const width = Math.min(400, window.innerWidth - 24);
    setPos({ top: r.bottom + 8, left: Math.min(Math.max(12, r.left - 10), window.innerWidth - width - 12), width });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const close = () => { setOpen(false); setPinned(false); };
    const key = (e: KeyboardEvent) => { if (e.key === "Escape") { close(); btn.current?.focus(); } };
    const down = (e: MouseEvent) => { if (wrap.current && !wrap.current.contains(e.target as Node)) close(); };
    const scroll = (e: Event) => { if (!wrap.current?.contains(e.target as Node)) close(); };
    window.addEventListener("keydown", key);
    document.addEventListener("mousedown", down);
    window.addEventListener("scroll", scroll, true);
    window.addEventListener("resize", close);
    return () => { window.removeEventListener("keydown", key); document.removeEventListener("mousedown", down); window.removeEventListener("scroll", scroll, true); window.removeEventListener("resize", close); };
  }, [open]);

  return (
    <span className="infotip" ref={wrap} onMouseEnter={() => show()} onMouseLeave={() => hide()}>
      <button ref={btn} type="button" className={`info-btn${open ? " on" : ""}`} aria-label={`About ${help.title}`} aria-expanded={open} aria-describedby={open ? id : undefined}
        onFocus={() => show(0)} onBlur={() => hide(0)}
        onClick={() => { window.clearTimeout(timer.current); if (open && pinned) { setOpen(false); setPinned(false); } else { setOpen(true); setPinned(true); } }}>
        <Info className="ic" />
      </button>
      {open && (
        <div id={id} role="tooltip" className="info-panel" style={pos ? { top: pos.top, left: pos.left, width: pos.width } : { visibility: "hidden" }}>
          <div className="ip-title">{help.title}</div>
          <p className="ip-lead">{help.lead}</p>
          {help.points && help.points.length > 0 && <ul className="ip-points">{help.points.map((p, i) => <li key={i}>{p}</li>)}</ul>}
          {help.note && <div className="ip-note"><b>Good to know</b>{help.note}</div>}
        </div>
      )}
    </span>
  );
}
