import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { AlertTriangle, ArrowLeft, Check, DatabaseZap, EyeOff, FileText, GitMerge, Info, Link2, ListPlus, Plus, Send, Shapes, ShieldAlert, Trash2, Unlink, Users, XCircle } from "lucide-react";
import { api, errText, send } from "../api";
import { useAuth } from "../auth";
import { Bi, EmptyState, Modal, SearchInput, StatusChip, Tags, Text, ValueChips, csv, hasArabic, useTitle, useToast } from "../ui";

const TABS = [["meaning", "Meaning", FileText], ["values", "Values", ListPlus], ["families", "Families", GitMerge], ["applies", "Applies to", Users], ["used", "Used in", Link2]] as const;
type Tab = (typeof TABS)[number][0];

function useDimension(id: string) {
  const qc = useQueryClient();
  const toast = useToast();
  const q = useQuery({ queryKey: ["dimension", id], queryFn: () => api<any>(`/api/dimensions/${id}`) });
  const done = (d: any) => { qc.setQueryData(["dimension", id], d); ["dimensions", "table", "preview"].forEach((k) => qc.invalidateQueries({ queryKey: [k] })); };
  const patch = useMutation({ mutationFn: (body: object) => send("PATCH", `/api/dimensions/${id}`, body), onSuccess: done, onError: (e) => toast(errText(e), true) });
  return { ...q, patch, done };
}

/* ------------------------------------------------------------------ values */
function LoadValuesDialog({ dim, onClose, onAdded }: { dim: any; onClose: () => void; onAdded: (d: any) => void }) {
  const toast = useToast();
  const [pick, setPick] = useState<Set<string>>(new Set());
  const load = useQuery({
    queryKey: ["load-values", dim.id], retry: false, staleTime: 0, gcTime: 0,
    queryFn: async () => {
      const r = await send("POST", `/api/dimensions/${dim.id}/load-values`, {});
      setPick(new Set((r.values as any[]).filter((v) => !v.in_vocabulary).map((v) => v.value)));
      return r;
    },
  });
  const add = useMutation({
    mutationFn: () => send("POST", `/api/dimensions/${dim.id}/values/bulk`, { values: [...pick].map((value) => ({ value })) }),
    onSuccess: (r: any) => { toast(`Added ${r.added} value${r.added === 1 ? "" : "s"} to the vocabulary`); onAdded(r.dimension); onClose(); },
    onError: (e) => toast(errText(e), true),
  });
  const r = load.data;
  const toggle = (v: string) => setPick((p) => { const n = new Set(p); n.has(v) ? n.delete(v) : n.add(v); return n; });
  return (
    <Modal title="Values in the data" sub="Read from the lake — the safe way to author an alias is to point it at a value you can see here" onClose={onClose} width={760}
      footer={<><button className="btn" onClick={onClose}>Close</button><button className="btn primary" disabled={!pick.size || add.isPending} onClick={() => add.mutate()}><Plus className="ic" />Add {pick.size} to the vocabulary</button></>}>
      {load.isFetching && <div className="loading">Reading values from the lake…</div>}
      {load.isError && <div className="banner bad"><AlertTriangle className="ic" /><span>{errText(load.error)}</span></div>}
      {r && (
        <>
          {r.errors.map((e: any) => <div key={e.column} className="banner bad"><XCircle className="ic" /><span><b>{e.column}</b> could not be read: {e.error}</span></div>)}
          {r.skipped.map((s: any) => <div key={s.column} className="banner"><EyeOff className="ic" /><span><b>{s.column}</b> was skipped — {s.reason}.</span></div>)}
          {r.truncated && <div className="banner"><Info className="ic" /><span>There are more than 200 distinct values; only the most frequent are shown.</span></div>}
          {r.values.length > 0 && (
            <div className="grid-wrap" style={{ maxHeight: 340 }}>
              <table className="grid">
                <thead><tr><th style={{ width: 30 }} /><th>Stored value</th><th className="num">Rows</th><th>Status</th><th>Found in</th></tr></thead>
                <tbody>
                  {r.values.map((v: any) => (
                    <tr key={v.value}>
                      <td>{!v.in_vocabulary && <input type="checkbox" aria-label={`Add ${v.value}`} checked={pick.has(v.value)} onChange={() => toggle(v.value)} />}</td>
                      <td><b style={{ fontFamily: "var(--mono)" }}>{v.value}</b></td>
                      <td className="num">{v.count.toLocaleString()}</td>
                      <td>{v.in_vocabulary ? <span className="chip ok">in the vocabulary</span> : <span className="chip gold-soft">new</span>}</td>
                      <td className="sub">{v.columns.join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {!load.isFetching && !r.values.length && !r.errors.length && <p className="muted">No values were read.</p>}
          {r.missing_from_data.length > 0 && <div className="banner" style={{ marginTop: 12 }}><Info className="ic" /><span>Listed here but not seen in the data: <b>{r.missing_from_data.join(", ")}</b>.</span></div>}
          <p className="sub" style={{ marginTop: 10 }}>{r.sampled}</p>
        </>
      )}
    </Modal>
  );
}

function RemoveValueDialog({ dim, value, onClose, onDone }: { dim: any; value: any; onClose: () => void; onDone: (d: any) => void }) {
  const toast = useToast();
  const dep = useQuery({ queryKey: ["value-dep", dim.id, value.id], queryFn: () => api<any>(`/api/dimensions/${dim.id}/values/${value.id}/dependents`), gcTime: 0 });
  const del = useMutation({
    mutationFn: () => send("DELETE", `/api/dimensions/${dim.id}/values/${value.id}?confirm=true`),
    onSuccess: (r: any) => { toast(`Removed ${value.value}${r.families_dropped.length ? ` · dropped the family ${r.families_dropped.join(", ")}` : ""}`); onDone(r.dimension); onClose(); },
    onError: (e) => toast(errText(e), true),
  });
  const d = dep.data;
  return (
    <Modal title={`Remove “${value.value}”?`} onClose={onClose} width={520}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className="btn danger-solid" disabled={!d || d.blocking || del.isPending} onClick={() => del.mutate()}><Trash2 className="ic" />Remove</button></>}>
      {!d ? <div className="loading">Checking what depends on it…</div> : (
        <>
          {d.blocking ? (
            <div className="banner bad"><ShieldAlert className="ic" /><span>This value is used by the “applies to” rule of <b>{d.applies_to.map((a: any) => a.dimension).join(", ")}</b>. Those rules change reported numbers, so change them first.</span></div>
          ) : d.aliases || d.families.length ? (
            <div className="banner"><AlertTriangle className="ic" /><span>Removing it also removes{d.aliases ? <> its <b>{d.aliases} alias{d.aliases === 1 ? "" : "es"}</b></> : null}{d.aliases && d.families.length ? " and" : ""}{d.families.length ? <> takes it out of the famil{d.families.length === 1 ? "y" : "ies"} <b>{d.families.join(", ")}</b> (a family left with one value is dropped)</> : null}.</span></div>
          ) : <p style={{ margin: 0 }}>Nothing else depends on this value.</p>}
        </>
      )}
    </Modal>
  );
}

function ValuesTab({ d, canEdit, onChange }: { d: any; canEdit: boolean; onChange: (d: any) => void }) {
  const toast = useToast();
  const [filter, setFilter] = useState("");
  const [removing, setRemoving] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [nv, setNv] = useState({ value: "", label: "", label_ar: "", aliases: [] as string[] });
  const edit = useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) => send("PATCH", `/api/dimensions/${d.id}/values/${id}`, body),
    onSuccess: onChange, onError: (e) => toast(errText(e), true),
  });
  const add = useMutation({
    mutationFn: () => send("POST", `/api/dimensions/${d.id}/values`, { ...nv, label: nv.label || null, label_ar: nv.label_ar || null }),
    onSuccess: (r) => { onChange(r); setNv({ value: "", label: "", label_ar: "", aliases: [] }); },
    onError: (e) => toast(errText(e), true),
  });
  const rows = d.values_list.filter((v: any) => !filter || `${v.value} ${v.label ?? ""} ${v.label_ar ?? ""} ${v.aliases.join(" ")}`.toLowerCase().includes(filter.toLowerCase()));
  const cell = (v: any, field: "label" | "label_ar", rtl?: boolean) => (
    <input className="cell" dir={rtl ? "rtl" : undefined} readOnly={!canEdit} defaultValue={v[field] ?? ""} key={`${v.id}-${field}-${v[field]}`} aria-label={`${field === "label" ? "English" : "Arabic"} label of ${v.value}`}
      onBlur={(e) => e.target.value !== (v[field] ?? "") && edit.mutate({ id: v.id, body: { [field]: e.target.value || null } })} />
  );
  return (
    <section className="card">
      <div style={{ display: "flex", gap: 12, alignItems: "flex-start", flexWrap: "wrap" }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h3><ListPlus className="ic" />Vocabulary <span className="count-pill">{d.values_list.length}</span></h3>
          <p className="hint" style={{ marginBottom: 0 }}>The left of each row is the value <b>as stored in the data</b>. The words on the right are what people might say or type, in either language. Aliases work in both languages.</p>
        </div>
        {canEdit && <button className="btn" disabled={!d.bindings_list.length} title={d.bindings_list.length ? "" : "Link at least one column first (Used in)"} onClick={() => setLoading(true)}><DatabaseZap className="ic" />Load values from the data</button>}
      </div>
      {d.values_list.length > 8 && <div className="filterbar"><SearchInput value={filter} onChange={setFilter} placeholder="Filter values…" label="Filter values" width={260} /></div>}
      <div className="grid-wrap" style={{ marginTop: 12 }}>
        <table className="grid vtable">
          <thead><tr><th style={{ width: 170 }}>Stored value</th><th style={{ width: 170 }}>Label · English</th><th style={{ width: 170 }}>Label · عربي</th><th>Words people use</th>{canEdit && <th style={{ width: 44 }} />}</tr></thead>
          <tbody>
            {rows.map((v: any) => (
              <tr key={v.id}>
                <td><b style={{ fontFamily: "var(--mono)", color: "var(--petrol)" }}>{v.value}</b></td>
                <td>{cell(v, "label")}</td>
                <td>{cell(v, "label_ar", true)}</td>
                <td><Tags value={v.aliases} disabled={!canEdit} label={`Words people use for ${v.value}`} placeholder="Add a word, press Enter" onChange={(aliases) => edit.mutate({ id: v.id, body: { aliases } })} /></td>
                {canEdit && <td><button className="btn ghost icon-only" aria-label={`Remove ${v.value}`} onClick={() => setRemoving(v)}><Trash2 className="ic" /></button></td>}
              </tr>
            ))}
            {canEdit && (
              <tr>
                <td><input className="cell" style={{ fontFamily: "var(--mono)", borderColor: "var(--line)" }} placeholder="STORED_VALUE" aria-label="New stored value" value={nv.value} onChange={(e) => setNv({ ...nv, value: e.target.value })} /></td>
                <td><input className="cell" style={{ borderColor: "var(--line)" }} placeholder="English label" aria-label="New English label" value={nv.label} onChange={(e) => setNv({ ...nv, label: e.target.value })} /></td>
                <td><input className="cell" dir="rtl" style={{ borderColor: "var(--line)" }} placeholder="التسمية" aria-label="New Arabic label" value={nv.label_ar} onChange={(e) => setNv({ ...nv, label_ar: e.target.value })} /></td>
                <td><Tags value={nv.aliases} label="Words for the new value" placeholder="Words people use…" onChange={(aliases) => setNv({ ...nv, aliases })} /></td>
                <td><button className="btn primary icon-only" aria-label="Add value" disabled={!nv.value.trim() || add.isPending} onClick={() => add.mutate()}><Plus className="ic" /></button></td>
              </tr>
            )}
            {!d.values_list.length && !canEdit && <tr><td colSpan={5} className="muted" style={{ padding: 20, textAlign: "center" }}>No values listed.</td></tr>}
          </tbody>
        </table>
      </div>
      {loading && <LoadValuesDialog dim={d} onClose={() => setLoading(false)} onAdded={onChange} />}
      {removing && <RemoveValueDialog dim={d} value={removing} onClose={() => setRemoving(null)} onDone={onChange} />}
    </section>
  );
}

/* ------------------------------------------------------------------ families */
function FamiliesTab({ d, canEdit, patch }: { d: any; canEdit: boolean; patch: any }) {
  const options: string[] = d.values_list.map((v: any) => v.value);
  const [fams, setFams] = useState<any[]>(d.families);
  useEffect(() => setFams(d.families), [d.families]);
  const dirty = JSON.stringify(fams) !== JSON.stringify(d.families);
  const set = (i: number, patchF: object) => setFams(fams.map((f, j) => (j === i ? { ...f, ...patchF } : f)));
  const bad = fams.some((f) => !f.term?.trim() || (f.values ?? []).length < 2);
  return (
    <section className="card">
      <h3><GitMerge className="ic" />Family terms <span className="count-pill">{d.families.length}</span></h3>
      <p className="hint">One business word that stands for <b>several</b> values — for example “gulf residents” = GCC and EXPAT. Unlike an alias, the term is shown to the planner so it knows the word exists. A family needs at least two values.</p>
      {fams.map((f, i) => (
        <div className="fam" key={i}>
          <div className="fam-head">
            <Text label="Term · English" value={f.term ?? ""} onSave={(v) => set(i, { term: v })} />
            <Text rtl label="المصطلح · عربي" value={f.term_ar ?? ""} onSave={(v) => set(i, { term_ar: v })} />
            {canEdit && <button className="btn danger icon-only" aria-label="Remove this family" onClick={() => setFams(fams.filter((_, j) => j !== i))}><Trash2 className="ic" /></button>}
          </div>
          <div className="field"><label>Stands for ({(f.values ?? []).length} selected)</label><ValueChips options={options} value={f.values ?? []} disabled={!canEdit} onChange={(values) => set(i, { values })} /></div>
        </div>
      ))}
      {!fams.length && <EmptyState icon={GitMerge} title="No family terms">Add one when a single word should mean several values.</EmptyState>}
      {canEdit && (
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={() => setFams([...fams, { term: "", term_ar: "", values: [] }])}><Plus className="ic" />Add a family</button>
          <button className="btn primary" disabled={!dirty || bad || patch.isPending} onClick={() => patch.mutate({ families: fams.map((f) => ({ term: f.term.trim(), term_ar: f.term_ar?.trim() || null, values: f.values })) })}><Check className="ic" />Save families</button>
          {dirty && bad && <span className="muted" style={{ alignSelf: "center" }}>Each family needs a term and two or more values.</span>}
        </div>
      )}
    </section>
  );
}

/* ------------------------------------------------------------------ applies to */
function ConditionRow({ c, all, canEdit, onChange, onRemove }: { c: any; all: any[]; canEdit: boolean; onChange: (c: any) => void; onRemove: () => void }) {
  const ref = all.find((x) => x.key === c.dimension);
  const detail = useQuery({ queryKey: ["dimension", String(ref?.id)], enabled: !!ref, queryFn: () => api<any>(`/api/dimensions/${ref.id}`) });
  const options: string[] = detail.data?.values_list.map((v: any) => v.value) ?? [];
  return (
    <div className="cond">
      <div className="field">
        <label>Only where</label>
        <select value={c.dimension} disabled={!canEdit} onChange={(e) => onChange({ dimension: e.target.value, values: [] })} aria-label="Dimension to restrict by">
          <option value="">Choose a dimension…</option>
          {all.map((x) => <option key={x.key} value={x.key}>{x.label || x.key} ({x.key})</option>)}
        </select>
      </div>
      <div className="field"><label>is one of</label>{c.dimension ? <ValueChips options={options} value={c.values} disabled={!canEdit} onChange={(values) => onChange({ ...c, values })} /> : <span className="muted">Pick a dimension first.</span>}</div>
      {canEdit && <button className="btn danger icon-only" aria-label="Remove this condition" onClick={onRemove}><Trash2 className="ic" /></button>}
    </div>
  );
}

function AppliesTab({ d, canEdit, patch }: { d: any; canEdit: boolean; patch: any }) {
  const all = useQuery({ queryKey: ["dimensions", ""], queryFn: () => api<any[]>("/api/dimensions?q=") });
  const [restrict, setRestrict] = useState(d.applies_to.length > 0);
  const [conds, setConds] = useState<any[]>(d.applies_to);
  const [note, setNote] = useState(d.applies_note ?? "");
  const [noteAr, setNoteAr] = useState(d.applies_note_ar ?? "");
  useEffect(() => { setConds(d.applies_to); setRestrict(d.applies_to.length > 0); setNote(d.applies_note ?? ""); setNoteAr(d.applies_note_ar ?? ""); }, [d.applies_to, d.applies_note, d.applies_note_ar]);
  const clean = restrict ? conds.filter((c) => c.dimension) : [];
  const incomplete = restrict && (clean.length === 0 || clean.some((c) => !c.values.length));
  const dirty = JSON.stringify(clean) !== JSON.stringify(d.applies_to) || note !== (d.applies_note ?? "") || noteAr !== (d.applies_note_ar ?? "");
  const pv = d.applies_preview;
  return (
    <section className="card">
      <h3><Users className="ic" />Who does this apply to?</h3>
      <p className="hint">Answers grouped by this dimension should be limited to the population it applies to, and shares measured against that population — so this changes reported numbers, not just wording. Agents receive it as an explicit instruction; the application does not run the query.</p>
      <div className="radio-cards" style={{ marginBottom: 14 }}>
        {[[false, "Everyone", "No restriction."], [true, "Only some people", "Restrict by values of another dimension — for example tribes exist for citizens only."]].map(([v, t, s]) => (
          <div key={String(v)} role="radio" aria-checked={restrict === v} tabIndex={0} className={`rcard${restrict === v ? " sel" : ""}`} onClick={() => canEdit && setRestrict(v as boolean)} onKeyDown={(e) => canEdit && (e.key === "Enter" || e.key === " ") && (e.preventDefault(), setRestrict(v as boolean))}>
            <div className="radio" /><div><b>{t as string}</b><span>{s as string}</span></div>
          </div>
        ))}
      </div>
      {restrict && (
        <>
          {conds.map((c, i) => <ConditionRow key={i} c={c} all={all.data ?? []} canEdit={canEdit} onChange={(n) => setConds(conds.map((x, j) => (j === i ? n : x)))} onRemove={() => setConds(conds.filter((_, j) => j !== i))} />)}
          {canEdit && <button className="btn" onClick={() => setConds([...conds, { dimension: "", values: [] }])}><Plus className="ic" />Add a condition</button>}
          <div className="two-col" style={{ marginTop: 14 }}>
            <div className="field"><label htmlFor="an">Note for agents · English (optional)</label><textarea id="an" rows={2} readOnly={!canEdit} value={note} onChange={(e) => setNote(e.target.value)} dir="auto" /></div>
            <div className="field ar"><label htmlFor="ana">ملاحظة للوكلاء (اختياري)</label><textarea id="ana" rows={2} dir="rtl" readOnly={!canEdit} value={noteAr} onChange={(e) => setNoteAr(e.target.value)} /></div>
          </div>
        </>
      )}
      {canEdit && (
        <div style={{ marginTop: 14, display: "flex", gap: 8, alignItems: "center" }}>
          <button className="btn primary" disabled={!dirty || incomplete || patch.isPending}
            onClick={() => patch.mutate({ applies_to: clean, applies_note: restrict ? note : null, applies_note_ar: restrict ? noteAr : null })}><Check className="ic" />Save</button>
          {incomplete && dirty && <span className="muted">Every condition needs a dimension and at least one value.</span>}
        </div>
      )}
      <h4 style={{ margin: "18px 0 8px", fontSize: 13, color: "var(--petrol)" }}>What agents are told</h4>
      {pv?.everyone ? <div className="instruction">Applies to everyone — no restriction.</div> : (
        <>
          <div className="instruction" dir="auto">{pv?.instruction}</div>
          {pv?.instruction_ar && <div className="instruction ar-text" dir="rtl" style={{ marginTop: 8 }}>{pv.instruction_ar}</div>}
        </>
      )}
    </section>
  );
}

/* ------------------------------------------------------------------ used in */
function BindDialog({ d, onClose, onDone }: { d: any; onClose: () => void; onDone: (d: any) => void }) {
  const toast = useToast();
  const [q, setQ] = useState("");
  const [pick, setPick] = useState<Set<number>>(new Set());
  const { data, isFetching } = useQuery({ queryKey: ["dim-columns", q], queryFn: () => api<any[]>(`/api/dimensions/columns?q=${encodeURIComponent(q)}&limit=60`), placeholderData: (p) => p });
  const bind = useMutation({
    mutationFn: () => send("POST", `/api/dimensions/${d.id}/bindings`, { column_ids: [...pick] }),
    onSuccess: (r) => { toast(`Linked ${pick.size} column${pick.size === 1 ? "" : "s"}`); onDone(r); onClose(); },
    onError: (e) => toast(errText(e), true),
  });
  const toggle = (id: number) => setPick((p) => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n; });
  return (
    <Modal title="Link columns" sub={`Columns that hold ${d.label || d.key} values`} onClose={onClose} width={720}
      footer={<><button className="btn" onClick={onClose}>Cancel</button><button className="btn primary" disabled={!pick.size || bind.isPending} onClick={() => bind.mutate()}><Link2 className="ic" />Link {pick.size || ""} column{pick.size === 1 ? "" : "s"}</button></>}>
      <SearchInput value={q} onChange={setQ} placeholder="Find a column or table…" label="Find a column" />
      <div className="grid-wrap" style={{ marginTop: 12, maxHeight: 360 }}>
        <table className="grid">
          <thead><tr><th style={{ width: 30 }} /><th>Column</th><th>Table</th><th>Type</th><th /></tr></thead>
          <tbody>
            {data?.map((c) => {
              const mine = c.bound_to === d.key, other = c.bound_to && !mine;
              return (
                <tr key={c.id} style={mine || other ? { opacity: 0.55 } : undefined}>
                  <td><input type="checkbox" aria-label={`Link ${c.column} in ${c.table}`} disabled={!!c.bound_to} checked={pick.has(c.id)} onChange={() => toggle(c.id)} /></td>
                  <td><b style={{ fontFamily: "var(--mono)" }}>{c.column}</b></td>
                  <td className="sub">{c.table}</td><td className="sub">{c.data_type}</td>
                  <td>{mine ? <span className="chip ok">already linked</span> : other ? <span className="chip">in {c.bound_to}</span> : c.pii ? <span className="chip warn with-ic"><ShieldAlert className="ic" />PII</span> : null}</td>
                </tr>
              );
            })}
            {data && !data.length && !isFetching && <tr><td colSpan={5} className="muted" style={{ padding: 20, textAlign: "center" }}>No columns match.</td></tr>}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}

function UsedTab({ d, canEdit, onChange }: { d: any; canEdit: boolean; onChange: (d: any) => void }) {
  const toast = useToast();
  const [binding, setBinding] = useState(false);
  const unbind = useMutation({ mutationFn: (cid: number) => send("DELETE", `/api/dimensions/${d.id}/bindings/${cid}`), onSuccess: onChange, onError: (e) => toast(errText(e), true) });
  return (
    <section className="card">
      <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <h3><Link2 className="ic" />Columns that hold this dimension <span className="count-pill">{d.bindings_list.length}</span></h3>
          <p className="hint" style={{ marginBottom: 0 }}>The same dimension often appears in several fact tables. Linking the columns lets agents know where it lives, and lets you read the real values from the data. A column belongs to one dimension.</p>
        </div>
        {canEdit && <button className="btn primary" onClick={() => setBinding(true)}><Plus className="ic" />Link columns</button>}
      </div>
      <div className="grid-wrap" style={{ marginTop: 14 }}>
        <table className="grid">
          <thead><tr><th>Column</th><th>Table</th><th>Type</th><th>State</th>{canEdit && <th />}</tr></thead>
          <tbody>
            {d.bindings_list.map((b: any) => (
              <tr key={b.column_id}>
                <td><b style={{ fontFamily: "var(--mono)", color: "var(--petrol)" }}>{b.column}</b></td>
                <td><Link className="tname" to={`/tables/${b.table_id}?tab=columns`}>{b.table}</Link></td>
                <td className="sub">{b.data_type}</td>
                <td>
                  {b.dropped && <span className="chip warn">dropped from the lake</span>}{" "}
                  {b.hidden && <span className="chip hold with-ic"><EyeOff className="ic" />hidden</span>}{" "}
                  {b.pii && <span className="chip warn with-ic"><ShieldAlert className="ic" />PII</span>}{" "}
                  {b.table_status !== "published" && <span className="chip">table {b.table_status}</span>}
                </td>
                {canEdit && <td style={{ textAlign: "right" }}><button className="btn ghost" onClick={() => unbind.mutate(b.column_id)}><Unlink className="ic" />Unlink</button></td>}
              </tr>
            ))}
            {!d.bindings_list.length && <tr><td colSpan={5}><EmptyState icon={Link2} title="Not linked to any column yet">Link the columns that hold these values to read real values from the data and tell agents where it lives.</EmptyState></td></tr>}
          </tbody>
        </table>
      </div>
      {binding && <BindDialog d={d} onClose={() => setBinding(false)} onDone={onChange} />}
    </section>
  );
}

/* ------------------------------------------------------------------ page */
export default function DimensionEditor() {
  const { id = "" } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const { canEdit } = useAuth();
  const [sp, setSp] = useSearchParams();
  const tab = (TABS.find((t) => t[0] === sp.get("tab"))?.[0] ?? "meaning") as Tab;
  const { data: d, isLoading, patch, done } = useDimension(id);
  const del = useMutation({
    mutationFn: () => send("DELETE", `/api/dimensions/${id}`),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["dimensions"] }); toast("Dimension deleted"); nav("/dimensions"); },
    onError: (e) => toast(errText(e), true),
  });
  useTitle(d ? d.label || d.key : "Dimension");
  const errs = useMemo(() => (d?.issues ?? []).filter((i: any) => i.severity === "error"), [d]);
  if (isLoading) return <div className="loading">Loading dimension…</div>;
  if (!d) return <div className="loading">Dimension not found.</div>;
  const p = (body: object) => patch.mutate(body);

  return (
    <div>
      <div className="te-head">
        <div className="te-head-inner wide">
          <div className="sub" style={{ marginBottom: 4 }}><Link className="crumb es-inline" to="/dimensions"><ArrowLeft className="ic" />Dimensions</Link></div>
          <div className="d-head">
            <div style={{ minWidth: 0 }}>
              <div className="d-kind"><Shapes className="ic" />Dimension</div>
              <div className="d-title">{d.label || d.key}{d.label_ar && <span className="ar-text" dir="rtl" style={{ marginLeft: 14, fontWeight: 500 }}>{d.label_ar}</span>}</div>
              <div className="d-name">{d.key}</div>
            </div>
            {canEdit && (
              <div className="d-actions">
                <button className="btn danger" onClick={() => window.confirm(`Delete the dimension “${d.key}”, its ${d.values_list.length} values and its links? Columns and data are not touched.`) && del.mutate()}><Trash2 className="ic" />Delete</button>
                {d.status !== "published"
                  ? <button className="btn primary" onClick={() => p({ status: "published" })}><Send className="ic" />Publish to agents</button>
                  : <button className="btn" onClick={() => p({ status: "draft" })}><EyeOff className="ic" />Unpublish</button>}
              </div>
            )}
          </div>
          <div className="chips" style={{ alignItems: "center" }}>
            <StatusChip status={d.status} />
            <span className="chip">{d.values_list.length} values</span>
            <span className="chip">{d.bindings_list.length} columns</span>
            {d.families.length > 0 && <span className="chip">{d.families.length} famil{d.families.length === 1 ? "y" : "ies"}</span>}
            {d.applies_to.length > 0 && <span className="chip gold-soft with-ic"><Users className="ic" />restricted</span>}
          </div>
          <div className="tabs" role="tablist">
            {TABS.map(([k, label, Icon]) => (
              <button key={k} role="tab" aria-selected={tab === k} className={`tab${tab === k ? " on" : ""}`} onClick={() => setSp(k === "meaning" ? {} : { tab: k }, { replace: true })}>
                <Icon className="ic" />{label}
                {k === "values" && <span className="count-pill">{d.values_list.length}</span>}
                {k === "families" && d.families.length > 0 && <span className="count-pill">{d.families.length}</span>}
                {k === "used" && <span className="count-pill">{d.bindings_list.length}</span>}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="te-body wide">
        {d.issues.length > 0 && (
          <details className={`dim-banner${errs.length ? " error" : ""}`} open={errs.length > 0}>
            <summary><AlertTriangle className="ic" />{errs.length ? `${errs.length} problem${errs.length === 1 ? "" : "s"} to fix` : `${d.issues.length} thing${d.issues.length === 1 ? "" : "s"} worth checking`}</summary>
            {d.issues.map((i: any, n: number) => <div key={n} className={`issue ${i.severity}`}>{i.severity === "error" ? <XCircle className="ic" /> : <Info className="ic" />}<span>{i.message}</span></div>)}
          </details>
        )}

        {tab === "meaning" && (
          <section className="card">
            <h3>What it means</h3>
            <p className="hint">The planner reads this to decide when the dimension applies. State the scope rules in plain words — that is how routing mistakes get fixed.</p>
            <div className="fields">
              <Bi label="Label" en={d.label ?? ""} ar={d.label_ar ?? ""} onEn={(v) => p({ label: v || null })} onAr={(v) => p({ label_ar: v || null })} />
              <Bi label="Description" area en={d.description ?? ""} ar={d.description_ar ?? ""} onEn={(v) => p({ description: v || null })} onAr={(v) => p({ description_ar: v || null })} />
            </div>
            <h3 style={{ marginTop: 20 }}>Words that name this dimension</h3>
            <p className="hint">Used to recognise a request to break down by it — and to spot “all X”, which means no restriction rather than a filter.</p>
            <div className="two-col">
              <Text label="Synonyms · English (comma separated)" value={(d.synonyms ?? []).join(", ")} onSave={(v) => p({ synonyms: csv(v) })} />
              <Text rtl label="مرادفات · عربي (مفصولة بفاصلة)" value={(d.synonyms_ar ?? []).join("، ")} onSave={(v) => p({ synonyms_ar: csv(v) })} />
            </div>
          </section>
        )}
        {tab === "values" && <ValuesTab d={d} canEdit={canEdit} onChange={done} />}
        {tab === "families" && <FamiliesTab d={d} canEdit={canEdit} patch={patch} />}
        {tab === "applies" && <AppliesTab d={d} canEdit={canEdit} patch={patch} />}
        {tab === "used" && <UsedTab d={d} canEdit={canEdit} onChange={done} />}
      </div>
    </div>
  );
}
