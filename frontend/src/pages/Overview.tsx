import { useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api";
import {
  AlertTriangle, BookA, BookOpen, CheckCircle2, ChevronRight, Database, Gauge, History, KeyRound, Lightbulb, Shapes, Table2, Users, Webhook as WebhookIcon,
} from "lucide-react";
import { useAuth } from "../auth";
import { EmptyState, InfoTip, ago, parseDate, useTitle } from "../ui";
import { HELP } from "../help";

const pct = (x: number) => `${Math.round((x ?? 0) * 100)}%`;
const n = (x: number) => (x ?? 0).toLocaleString();
const plural = (c: number, one: string, many = `${one}s`) => `${n(c)} ${c === 1 ? one : many}`;
const DAY = 86400000;
const q = <T,>(key: string, path: string, enabled = true) => useQuery({ queryKey: [key], queryFn: () => api<T>(path), enabled, retry: false });

type Sev = "high" | "med" | "low";
type Item = { sev: Sev; text: string; to: string };

/** One-line bilingual coverage bar. */
function Bars({ en, ar }: { en: number; ar: number }) {
  return (
    <div className="ov-bars" aria-label={`English ${pct(en)}, Arabic ${pct(ar)}`}>
      <div><span>EN</span><i className="meter"><i style={{ width: pct(en) }} /></i><b>{pct(en)}</b></div>
      <div><span>AR</span><i className="meter ar"><i style={{ width: pct(ar) }} /></i><b>{pct(ar)}</b></div>
    </div>
  );
}

/** Stacked status bar with a legend. Segments with 0 are omitted. */
function Mix({ label, to, parts }: { label: string; to: string; parts: { name: string; value: number; cls: string }[] }) {
  const total = parts.reduce((a, p) => a + p.value, 0);
  return (
    <div className="ov-mix">
      <div className="ov-mix-head"><Link to={to}>{label}</Link><span className="muted">{n(total)} total</span></div>
      {total === 0 ? <div className="ov-mix-bar empty" /> : (
        <div className="ov-mix-bar" role="img" aria-label={parts.map((p) => `${p.value} ${p.name}`).join(", ")}>
          {parts.filter((p) => p.value > 0).map((p) => <i key={p.name} className={p.cls} style={{ flexGrow: p.value }} title={`${p.value} ${p.name}`} />)}
        </div>
      )}
      <div className="ov-legend">{parts.map((p) => <span key={p.name}><i className={p.cls} />{n(p.value)} {p.name}</span>)}</div>
    </div>
  );
}

export default function Overview() {
  useTitle("Overview");
  const { isAdmin, me } = useAuth();
  const stats = q<any>("stats", "/api/catalog/stats");
  const tree = q<any[]>("tree", "/api/catalog/tree");
  const metrics = q<any[]>("metrics", "/api/metrics");
  const dims = q<any[]>("dimensions-ov", "/api/dimensions");
  const gloss = q<any[]>("glossary-ov", "/api/glossary");
  const sources = q<any[]>("sources-ov", "/api/sources");
  const audit = q<any[]>("audit-ov", "/api/audit");
  const keys = q<any[]>("keys-ov", "/api/admin/keys", isAdmin);
  const users = q<any[]>("users-ov", "/api/admin/users", isAdmin);
  const hooks = q<any[]>("hooks-ov", "/api/admin/webhooks", isAdmin);
  const [by, setBy] = useState<"domain" | "source" | "type">("domain");
  const [all, setAll] = useState(false);

  const data = stats.data;
  const t = data?.totals;
  const w = data?.worklists;

  const M = metrics.data ?? [], D = dims.data ?? [], G = gloss.data ?? [], S = sources.data ?? [], K = keys.data ?? [], U = users.data ?? [], H = hooks.data ?? [];
  const mPub = M.filter((m) => m.status === "published").length;
  const mDraft = M.filter((m) => m.status === "draft").length;
  const mRev = M.filter((m) => m.status === "reviewed").length;
  const mNoTable = M.filter((m) => !m.base_table_id).length;
  const mNoAr = M.filter((m) => !(m.name_ar && m.description_ar)).length;
  const dPub = D.filter((d) => d.status === "published").length;
  const dDraft = D.filter((d) => d.status === "draft").length;
  const dRev = D.filter((d) => d.status === "reviewed").length;
  const dErr = D.reduce((a, d) => a + (d.errors ?? 0), 0);
  const dWarn = D.reduce((a, d) => a + (d.warnings ?? 0), 0);
  const dValues = D.reduce((a, d) => a + (d.values ?? 0), 0);
  const dLinks = D.reduce((a, d) => a + (d.bindings ?? 0), 0);
  const dRestricted = D.filter((d) => d.applies).length;

  const lastSync = S.map((s) => parseDate(s.last_synced_at)?.getTime() ?? 0).reduce((a, b) => Math.max(a, b), 0);
  const lastChange = audit.data?.[0];
  const keyUse = K.map((k) => parseDate(k.last_used_at)?.getTime() ?? 0).reduce((a, b) => Math.max(a, b), 0);
  const now = Date.now();
  const keysExpired = K.filter((k) => k.expires_at && parseDate(k.expires_at)!.getTime() < now).length;
  const keysSoon = K.filter((k) => k.expires_at && (parseDate(k.expires_at)!.getTime() - now) > 0 && (parseDate(k.expires_at)!.getTime() - now) < 14 * DAY).length;
  const keysUnused = K.filter((k) => !k.use_count).length;
  const hooksBad = H.filter((h) => h.is_active && h.last_status && /error|fail|timeout|refused|\b[45]\d\d\b/i.test(String(h.last_status))).length;

  // ---- what needs attention, most serious first
  const attention = useMemo<Item[]>(() => {
    if (!t) return [];
    const out: Item[] = [];
    const add = (sev: Sev, c: number | undefined, text: (c: number) => string, to: string) => { if (c && c > 0) out.push({ sev, text: text(c), to }); };
    for (const s of S) {
      if (!s.last_synced_at) out.push({ sev: "high", text: `Source “${s.name}” has never been synced`, to: "/sources" });
      else if (now - (parseDate(s.last_synced_at)?.getTime() ?? 0) > 7 * DAY) out.push({ sev: "med", text: `Source “${s.name}” was last synced ${ago(s.last_synced_at)}`, to: "/sources" });
    }
    add("high", t.quarantined_columns, (c) => `${plural(c, "column")} hidden from agents, waiting for your release`, "/quarantine");
    add("high", dErr, (c) => `${plural(c, "error")} in dimensions that agents rely on`, "/dimensions");
    add("high", keysExpired, (c) => `${plural(c, "API key")} expired`, "/settings?tab=keys");
    add("med", t.pending, (c) => `${plural(c, "table")} with edits waiting to be published`, "/changes");
    add("med", t.review, (c) => `${plural(c, "table")} new or changed since the last review`, "/catalog?needs_review=true");
    add("med", dWarn, (c) => `${plural(c, "warning")} in dimensions`, "/dimensions");
    add("med", w?.description, (c) => `${plural(c, "table")} without a description`, "/catalog?missing=description");
    add("med", w?.grain, (c) => `${plural(c, "table")} without a grain`, "/catalog?missing=grain");
    add("med", keysSoon, (c) => `${plural(c, "API key")} expiring within 14 days`, "/settings?tab=keys");
    add("med", hooksBad, (c) => `${plural(c, "webhook")} failing on the last delivery`, "/settings?tab=webhooks");
    add("low", w?.draft, (c) => `${plural(c, "table")} not published, so invisible to agents`, "/catalog?status=draft");
    add("low", mDraft + mRev, (c) => `${plural(c, "metric")} not published, so invisible to agents`, `/metrics?show=${mDraft ? "draft" : "reviewed"}`);
    add("low", mNoTable, (c) => `${plural(c, "metric")} without a base table`, "/metrics?show=no_table");
    add("low", w?.columns, (c) => `${plural(c, "table")} with undocumented columns`, "/catalog?missing=columns");
    add("low", t.no_arabic, (c) => `${plural(c, "table")} without any Arabic`, "/catalog?missing=arabic");
    add("low", mNoAr, (c) => `${plural(c, "metric")} missing an Arabic name or definition`, "/metrics?show=no_ar");
    add("low", dDraft + dRev, (c) => `${plural(c, "dimension")} not published`, "/dimensions");
    add("low", keysUnused, (c) => `${plural(c, "API key")} never used`, "/settings?tab=keys");
    if (gloss.isSuccess && G.length === 0) out.push({ sev: "low", text: "The glossary is empty. Add the words people use so agents can resolve them", to: "/glossary" });
    return out;
    // eslint-disable-next-line
  }, [t, w, S, M, D, G, K, H, dErr, dWarn, gloss.isSuccess]);
  const order: Record<Sev, number> = { high: 0, med: 1, low: 2 };
  const sorted = [...attention].sort((a, b) => order[a.sev] - order[b.sev]);
  const shownAttention = all ? sorted : sorted.slice(0, 7);

  if (stats.isError) return <div className="loading">Could not load the overview. Check your connection and refresh.</div>;
  if (!data) return <div className="loading">Loading overview…</div>;
  if (!t.tables) {
    return (
      <div style={{ paddingTop: 60 }}>
        <EmptyState icon={Database} title="No tables yet" actions={<Link className="btn primary" to="/sources">Add a source</Link>}>
          Connect a data lake source and sync it to start building the semantic layer.
        </EmptyState>
      </div>
    );
  }

  // ---- coverage breakdown (least documented first)
  const rows = [...(by === "domain" ? data.by_domain : by === "source" ? data.by_source : data.by_type)].sort((a, b) => (a.en + a.ar) - (b.en + b.ar));
  const link = (name: string) => by === "source" ? `/catalog?source_id=${tree.data?.find((s) => s.name === name)?.id ?? ""}`
    : by === "domain" ? (name === "(none)" ? "/catalog?missing=domain" : `/catalog?domain=${encodeURIComponent(name)}`)
    : (name === "(none)" ? "/catalog?missing=type" : `/catalog?type=${encodeURIComponent(name)}`);
  const weakest = [...data.by_domain].filter((d: any) => d.name !== "(none)").sort((a: any, b: any) => a.en - b.en)[0];

  const insights: { icon: any; text: ReactNode; to?: string }[] = [];
  insights.push({ icon: BookOpen, to: "/catalog", text: <>English documentation is <b>{pct(t.en)}</b> complete and Arabic <b>{pct(t.ar)}</b>{weakest ? <>. Least documented domain: <b>{weakest.name}</b> ({pct(weakest.en)} EN).</> : "."}</> });
  insights.push({ icon: History, to: isAdmin ? "/settings?tab=audit" : undefined, text: <>{lastSync ? <>Last synced <b>{ago(new Date(lastSync).toISOString())}</b>. </> : <>Never synced. </>}{lastChange ? <>Last catalog change <b>{ago(lastChange.at)}</b> by {actorLabel(lastChange.actor)}.</> : "No changes recorded yet."}</> });
  if (metrics.isSuccess) insights.push({ icon: Gauge, to: "/metrics", text: M.length ? <><b>{mPub}</b> of {M.length} metrics are live for agents; <b>{M.length - mNoAr}</b> have an Arabic definition.</> : <>No metrics yet. Governed metrics stop agents from inventing their own SQL.</> });
  if (dims.isSuccess && D.length) insights.push({ icon: Shapes, to: "/dimensions", text: <><b>{n(dValues)}</b> values across {plural(D.length, "dimension")}, linked to {plural(dLinks, "column")}; <b>{dRestricted}</b> restricted to specific audiences.</> });
  if (isAdmin && keys.isSuccess) insights.push({ icon: KeyRound, to: "/settings?tab=keys", text: K.length ? <><b>{plural(K.length, "application")}</b> can connect with an API key{keyUse ? <>; most recent use <b>{ago(new Date(keyUse).toISOString())}</b></> : <>; none has been used yet</>}.</> : <><b>No application has an API key yet.</b> Agents cannot connect until one is created.</> });

  const groups = groupActivity(audit.data ?? []).slice(0, 5);

  return (
    <div className="page ov">
      <div className="page-head">
        <div>
          <div className="d-kind"><Table2 className="ic" />Overview{me.org_name ? ` · ${me.org_name}` : ""}</div>
          <div className="d-title">Where the semantic layer stands <InfoTip help={HELP.overview} /></div>
        </div>
      </div>

      <div className="ov-kpis">
        <Kpi to="/catalog" icon={Table2} label="Tables" value={t.published} of={t.tables} sub={`${n(t.columns)} columns · ${t.tables - t.published ? `${n(t.tables - t.published)} not published` : "all published"}`} frac={t.published / t.tables} />
        <Kpi to="/metrics" icon={Gauge} label="Metrics" value={mPub} of={M.length} sub={M.length ? `${n(mDraft + mRev)} not published` : "none defined yet"} frac={M.length ? mPub / M.length : 0} loading={metrics.isLoading} />
        <Kpi to="/dimensions" icon={Shapes} label="Dimensions" value={dPub} of={D.length} sub={`${n(dValues)} values · ${dErr + dWarn ? `${n(dErr + dWarn)} issue${dErr + dWarn === 1 ? "" : "s"}` : "no issues"}`} frac={D.length ? dPub / D.length : 0} loading={dims.isLoading} />
        <Kpi to="/glossary" icon={BookA} label="Glossary terms" value={G.length} sub={G.length ? "synonyms agents can resolve" : "none yet"} loading={gloss.isLoading} />
        <Kpi to="/columns" icon={BookOpen} label="Columns documented" pctValue={pct(t.en)} sub={`${n(t.columns)} columns · AR ${pct(t.ar)}`} frac={t.en} />
      </div>

      <div className="ov-grid">
        <div className="ov-col">
          <section className="ov-card">
            <h3><AlertTriangle className="ic" />Needs your attention {sorted.length > 0 && <span className="count-pill">{sorted.length}</span>}</h3>
            {sorted.length === 0 ? (
              <div className="ov-clear"><CheckCircle2 className="ic" />All clear. Nothing is waiting on you.</div>
            ) : (
              <>
                <ul className="ov-list">
                  {shownAttention.map((it, i) => (
                    <li key={i}><Link to={it.to}><span className={`ov-dot ${it.sev}`} title={it.sev === "high" ? "Blocks agents or exposes data" : it.sev === "med" ? "Should be handled soon" : "Nice to fix"} /><span className="ov-t">{it.text}</span><span className="sr-only"> ({it.sev === "high" ? "high" : it.sev === "med" ? "medium" : "low"} priority)</span><ChevronRight className="ic" /></Link></li>
                  ))}
                </ul>
                {sorted.length > 7 && <button className="btn ghost ov-more" onClick={() => setAll(!all)}>{all ? "Show fewer" : `Show all ${sorted.length}`}</button>}
              </>
            )}
          </section>

          <section className="ov-card">
            <div className="ov-head">
              <h3><BookOpen className="ic" />Documentation coverage</h3>
              <div className="seg" role="group" aria-label="Break down by">
                {(["domain", "source", "type"] as const).map((k) => <button key={k} className={by === k ? "on" : ""} aria-pressed={by === k} onClick={() => setBy(k)}>{k === "type" ? "Table type" : k[0].toUpperCase() + k.slice(1)}</button>)}
              </div>
            </div>
            <div className="ov-total"><span>Overall</span><Bars en={t.en} ar={t.ar} /></div>
            <table className="grid ov-table">
              <thead><tr><th>{by === "type" ? "Table type" : by[0].toUpperCase() + by.slice(1)}</th><th className="num">Tables</th><th className="num">Published</th><th>Documented</th></tr></thead>
              <tbody>
                {rows.map((r: any) => (
                  <tr key={r.name}>
                    <td><Link className="tname" to={link(r.name)}>{r.name}</Link>{r.review ? <span className="chip warn ov-chip">{r.review} to review</span> : null}</td>
                    <td className="num">{n(r.tables)}</td><td className="num">{n(r.published)}</td>
                    <td><Bars en={r.en} ar={r.ar} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="ov-foot muted">Least documented first. Percentages count grains, types and column descriptions filled in.</div>
          </section>
        </div>

        <div className="ov-col">
          <section className="ov-card">
            <h3><Lightbulb className="ic" />Insights</h3>
            <ul className="ov-insights">
              {insights.map((x, i) => {
                const body = <><x.icon className="ic" /><span>{x.text}</span></>;
                return <li key={i}>{x.to ? <Link to={x.to}>{body}</Link> : <div>{body}</div>}</li>;
              })}
            </ul>
          </section>

          <section className="ov-card">
            <h3><Table2 className="ic" />Publishing status</h3>
            <Mix label="Tables" to="/catalog" parts={[{ name: "published", value: t.published, cls: "pub" }, { name: "not published", value: t.tables - t.published, cls: "draft" }]} />
            <Mix label="Metrics" to="/metrics" parts={[{ name: "published", value: mPub, cls: "pub" }, { name: "reviewed", value: mRev, cls: "rev" }, { name: "draft", value: mDraft, cls: "draft" }]} />
            <Mix label="Dimensions" to="/dimensions" parts={[{ name: "published", value: dPub, cls: "pub" }, { name: "reviewed", value: dRev, cls: "rev" }, { name: "draft", value: dDraft, cls: "draft" }]} />
          </section>

          <section className="ov-card">
            <div className="ov-head"><h3><History className="ic" />Recent activity</h3>{isAdmin && <Link className="ov-link" to="/settings?tab=audit">Audit log</Link>}</div>
            {groups.length === 0 ? <div className="muted">No changes recorded yet.</div> : (
              <ul className="ov-activity">
                {groups.map((g, i) => (
                  <li key={i}>
                    <div><b>{actorLabel(g.actor)}</b> <span className="muted">· {plural(g.count, "change")}</span></div>
                    <div className="sub">{g.summary} · {ago(g.at)}</div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {isAdmin && (
            <section className="ov-card">
              <h3><KeyRound className="ic" />Access &amp; integrations</h3>
              <ul className="ov-access">
                <li><Link to="/settings?tab=users"><Users className="ic" /><span>Users</span><b>{n(U.length)}</b><span className="muted">{U.filter((u) => u.role === "admin").length} admin · {U.filter((u) => u.is_active).length} active</span></Link></li>
                <li><Link to="/settings?tab=keys"><KeyRound className="ic" /><span>API keys</span><b>{n(K.length)}</b><span className="muted">{K.length ? (keyUse ? `used ${ago(new Date(keyUse).toISOString())}` : "never used") : "none created"}</span></Link></li>
                <li><Link to="/settings?tab=webhooks"><WebhookIcon className="ic" /><span>Webhooks</span><b>{n(H.length)}</b><span className="muted">{H.length ? (hooksBad ? `${hooksBad} failing` : "healthy") : "none configured"}</span></Link></li>
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function Kpi({ to, icon: Icon, label, value, of, pctValue, sub, frac, loading }: { to: string; icon: any; label: string; value?: number; of?: number; pctValue?: string; sub: string; frac?: number; loading?: boolean }) {
  return (
    <Link className="ov-kpi" to={to}>
      <div className="ov-kpi-top"><Icon className="ic" /><span>{label}</span></div>
      <div className="ov-kpi-v">{loading ? "…" : pctValue ?? n(value ?? 0)}{of !== undefined && !loading && <small> / {n(of)}</small>}</div>
      <div className="ov-kpi-sub">{sub}</div>
      {frac !== undefined && <div className="meter ov-kpi-meter" aria-hidden><i style={{ width: `${Math.round(Math.max(0, Math.min(1, frac)) * 100)}%` }} /></div>}
    </Link>
  );
}

const actorLabel = (a?: string | null) => (!a ? "someone" : a.startsWith("import:") ? `Import (${a.slice(7).split(":")[0]})` : a);

/** Collapse the raw audit trail into "who changed how much, and when": consecutive entries by the same actor within 30 minutes. */
function groupActivity(rows: any[]) {
  const out: { actor: string; count: number; at: string; kinds: Record<string, number>; summary: string }[] = [];
  for (const r of rows) {
    const last = out[out.length - 1];
    const at = parseDate(r.at)?.getTime() ?? 0;
    if (last && last.actor === r.actor && Math.abs((parseDate(last.at)?.getTime() ?? 0) - at) < 30 * 60000) { last.count++; last.kinds[r.entity] = (last.kinds[r.entity] ?? 0) + 1; }
    else out.push({ actor: r.actor, count: 1, at: r.at, kinds: { [r.entity]: 1 }, summary: "" });
  }
  for (const g of out) g.summary = Object.entries(g.kinds).map(([k, c]) => `${c} ${k}${c === 1 ? "" : "s"}`).join(", ");
  return out;
}
