import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, NavLink, Outlet, useLocation, useSearchParams } from "react-router-dom";
import {
  BookA, BookOpen, ChevronDown, EyeOff, GitPullRequestDraft, Shapes, ChevronRight, ClipboardCheck, Database, Eye, Folder, FolderTree, KeyRound, LayoutDashboard, Lock,
  LogOut, Menu as MenuIcon, Rocket, Settings as SettingsIcon, ShieldAlert, Table2, Gauge,
} from "lucide-react";
import { api, send } from "./api";
import { ChangePasswordDialog, SetupDialog, useAuth } from "./auth";
import { Avatar, ErrorBoundary, LangToggle, Menu, SaveIndicator, SearchInput } from "./ui";

export default function Layout() {
  const loc = useLocation();
  const [sp] = useSearchParams();
  const [q, setQ] = useState("");
  const { me, isAdmin, canEdit, refresh } = useAuth();
  const [setup, setSetup] = useState(false);
  const [pw, setPw] = useState(false);
  const [navOpen, setNavOpen] = useState(false);
  const [open, setOpen] = useState<Record<string, boolean>>(() => {
    try { return JSON.parse(localStorage.getItem("sl.tree") ?? "{}"); } catch { return {}; }
  });
  useEffect(() => { try { localStorage.setItem("sl.tree", JSON.stringify(open)); } catch { /* ignore */ } }, [open]);

  // the sidebar is a slide-over drawer on narrow screens: close it after navigating, and on Escape
  useEffect(() => { setNavOpen(false); }, [loc.pathname, loc.search]);
  useEffect(() => {
    if (!navOpen) return;
    const h = (e: KeyboardEvent) => e.key === "Escape" && setNavOpen(false);
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [navOpen]);

  // "/" jumps to the page's search box, like most pro tools
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      if (e.key !== "/" || e.metaKey || e.ctrlKey || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable) return;
      const box = document.querySelector<HTMLInputElement>("[data-searchbox]");
      if (box) { e.preventDefault(); box.focus(); box.select(); }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, []);

  const tree = useQuery({ queryKey: ["tree"], queryFn: () => api<any[]>("/api/catalog/tree") });
  const stats = useQuery({ queryKey: ["stats"], queryFn: () => api<any>("/api/catalog/stats") });
  const dimensions = useQuery({ queryKey: ["dimensions", ""], queryFn: () => api<any[]>("/api/dimensions?q=") });
  const reviewQ = useQuery({ queryKey: ["review"], queryFn: () => api<any>("/api/review") });
  const t = stats.data?.totals;

  const needle = q.trim().toLowerCase();
  const sourceCount = tree.data?.length ?? 0;
  const activeSource = sp.get("source_id");
  const isOpen = (id: number) => (needle ? true : open[id] ?? (sourceCount === 1 || String(id) === activeSource));
  const onCatalog = loc.pathname === "/catalog";
  const display = me.user?.name || me.user?.email || "";

  return (
    <div className="app">
      <a className="skip-link" href="#main" onClick={(e) => { e.preventDefault(); const m = document.getElementById("main"); m?.focus(); m?.scrollIntoView(); }}>Skip to content</a>
      <header>
        <button className="nav-toggle" aria-label="Menu" aria-expanded={navOpen} aria-controls="side-nav" onClick={() => setNavOpen((o) => !o)}><MenuIcon className="ic" /></button>
        <div className="brand">
          <img className="logo" src="/vendor/icp-logo.png" alt="ICP" />
          <div className="divider" />
          <div className="masthead">
            <div className="title">Semantic Layer</div>
            <div className="sub">{me.org_name ? `${me.org_name} · What agents know about the data lake` : "What agents know about the data lake"}</div>
          </div>
        </div>
        <div className="head-spacer" />
        {t && (
          <div className="totals">
            <span title="Tables in the catalog"><Table2 className="ic" /><b>{t.tables.toLocaleString()}</b> {t.tables === 1 ? "table" : "tables"}</span>
            <span title="Visible to agents"><Rocket className="ic" /><b>{t.published.toLocaleString()}</b> published</span>
            <span title="New or changed since last review"><ClipboardCheck className="ic" /><b>{t.review.toLocaleString()}</b> to review</span>
          </div>
        )}
        <SaveIndicator />
        <LangToggle />
        {me.user && (
          <Menu label={<><Avatar name={display} size={26} /><span>{display}</span></>} className="user-sum">{(close) => (
            <>
              <div className="who"><Avatar name={display} size={36} /><div><b style={{ display: "block", fontSize: 13 }}>{display}</b><span className="sub">{me.user!.email} · {me.user!.role}</span></div></div>
              <div className="sep" />
              <button className="mi" onClick={() => { setPw(true); close(); }}><KeyRound className="ic" />Change password</button>
              <button className="mi" onClick={async () => { close(); await send("POST", "/api/auth/logout"); refresh(); }}><LogOut className="ic" />Sign out</button>
            </>
          )}</Menu>
        )}
      </header>
      {me.setup_needed && isAdmin && (
        <div className="topbar warn">
          <span><ShieldAlert className="ic" /><span><b>This catalog is open.</b> Anyone with this address can edit it, and applications can read it without a key.</span></span>
          <button className="btn" onClick={() => setSetup(true)}><Lock className="ic" />Secure this catalog</button>
        </div>
      )}
      {!canEdit && <div className="topbar"><span><Eye className="ic" /><span>You have <b>read-only</b> access. Ask an administrator if you need to make changes.</span></span></div>}

      <div className="frame">
        {navOpen && <div className="nav-scrim" onClick={() => setNavOpen(false)} />}
        <aside className={`nav${navOpen ? " open" : ""}`} id="side-nav">
          <div className="search-box">
            <SearchInput value={q} onChange={setQ} placeholder="Find a source or schema…" label="Filter sources and schemas" />
          </div>
          <nav className="nav-top" aria-label="Main">
            <NavLink className="nav-link" to="/" end><LayoutDashboard className="ic" />Overview</NavLink>
            <Link className={`nav-link${onCatalog && !sp.get("source_id") && !sp.get("needs_review") ? " active" : ""}`} to="/catalog"><Table2 className="ic" />All tables <span className="count-pill">{t?.tables ?? 0}</span></Link>
            <Link className={`nav-link${sp.get("needs_review") ? " active" : ""}`} to="/catalog?needs_review=true"><ClipboardCheck className="ic" />Review queue <span className="count-pill">{t?.review ?? 0}</span></Link>
            <NavLink className="nav-link" to="/changes"><GitPullRequestDraft className="ic" />Pending changes <span className="count-pill">{(t?.pending ?? 0) + (reviewQ.data?.total ?? 0)}</span></NavLink>
            <NavLink className="nav-link" to="/quarantine"><EyeOff className="ic" />Quarantine <span className="count-pill">{t?.quarantined_columns ?? 0}</span></NavLink>
            <NavLink className="nav-link" to="/dimensions"><Shapes className="ic" />Dimensions <span className="count-pill">{dimensions.data?.length ?? 0}</span></NavLink>
            <NavLink className="nav-link" to="/columns"><BookOpen className="ic" />Column dictionary</NavLink>
            <NavLink className="nav-link" to="/metrics"><Gauge className="ic" />Metrics</NavLink>
            <NavLink className="nav-link" to="/glossary"><BookA className="ic" />Glossary</NavLink>
            <div className="nav-sep" />
            <NavLink className="nav-link" to="/sources"><Database className="ic" />Sources</NavLink>
            {isAdmin && <NavLink className="nav-link" to="/settings"><SettingsIcon className="ic" />Settings</NavLink>}
          </nav>
          <div className="nav-scroll">
            <div className="nav-group"><FolderTree className="ic" style={{ width: 12, height: 12, verticalAlign: -1, marginInlineEnd: 6 }} />Sources & schemas</div>
            {tree.data?.map((src) => {
              const schemas = src.schemas.filter((s: any) => !needle || s.name.toLowerCase().includes(needle) || src.name.toLowerCase().includes(needle));
              if (needle && !schemas.length) return null;
              const expanded = isOpen(src.id);
              return (
                <div className="tree-src" key={src.id}>
                  <button className="src" aria-expanded={expanded} onClick={() => setOpen({ ...open, [src.id]: !expanded })}>
                    {expanded ? <ChevronDown className="caret" /> : <ChevronRight className="caret" />}
                    <Database className="ic" />
                    <span style={{ flex: 1, textAlign: "left" }}>{src.name}</span>
                    <span className="count-pill">{src.tables}</span>
                  </button>
                  {expanded && (
                    <>
                      <Link className={`tree-schema${onCatalog && sp.get("source_id") === String(src.id) && !sp.get("schema") ? " active" : ""}`} to={`/catalog?source_id=${src.id}`}>
                        <Folder className="ic" /><span className="nm"><i>all schemas</i></span>
                      </Link>
                      {schemas.map((s: any) => (
                        <Link key={s.name} title={`${s.tables} tables · EN ${Math.round(s.en * 100)}% · عربي ${Math.round(s.ar * 100)}%`}
                          className={`tree-schema${onCatalog && sp.get("source_id") === String(src.id) && sp.get("schema") === s.name ? " active" : ""}`}
                          to={`/catalog?source_id=${src.id}&schema=${encodeURIComponent(s.name)}`}>
                          <Folder className="ic" />
                          <span className="nm">{s.name}</span>
                          <span className="dots"><i className={`dot-s${s.en > 0.66 ? " en" : ""}`} /><i className={`dot-s${s.ar > 0.66 ? " ar" : ""}`} /></span>
                          <span className="count-pill">{s.tables}</span>
                        </Link>
                      ))}
                    </>
                  )}
                </div>
              );
            })}
            {tree.isSuccess && !tree.data.length && <div className="nav-group">No sources yet</div>}
          </div>
        </aside>
        <main id="main" tabIndex={-1}><ErrorBoundary key={loc.pathname}><Outlet /></ErrorBoundary></main>
      </div>
      {setup && <SetupDialog onClose={() => setSetup(false)} onDone={() => { setSetup(false); refresh(); }} />}
      {(pw || me.user?.must_change_password) && <ChangePasswordDialog forced={!pw} onClose={() => setPw(false)} />}
    </div>
  );
}
