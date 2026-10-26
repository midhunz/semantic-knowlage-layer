import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, errText, send } from "../../api";
import { Bot, Building2, Check, EyeOff, Lock, Rocket } from "lucide-react";
import { Switch, useToast } from "../../ui";

type S = { pii_name_patterns: string; revision_requires_different_approver: boolean; org_name: string; default_lang: string; default_max_tokens: number; pii_columns_in_agent_output: string; require_review_before_publish: boolean; min_completeness_to_publish: number; session_hours: number };

function Choice({ value, current, onPick, title, text }: { value: string; current: string; onPick: (v: string) => void; title: string; text: string }) {
  return (
    <div className={`rcard${current === value ? " sel" : ""}`} role="radio" aria-checked={current === value} tabIndex={0} onClick={() => onPick(value)} onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), onPick(value))}>
      <div className="radio" /><div><b>{title}</b><span>{text}</span></div>
    </div>
  );
}

export default function General() {
  const qc = useQueryClient();
  const toast = useToast();
  const { data } = useQuery({ queryKey: ["settings"], queryFn: () => api<S>("/api/admin/settings") });
  const [f, setF] = useState<S | null>(null);
  useEffect(() => { if (data) setF(data); }, [data]);
  const save = useMutation({
    mutationFn: () => send("PUT", "/api/admin/settings", f),
    onSuccess: (r) => { qc.setQueryData(["settings"], r); qc.invalidateQueries({ queryKey: ["me"] }); toast("Settings saved"); },
    onError: (e) => toast(errText(e), true),
  });
  if (!f || !data) return <div className="loading">Loading…</div>;
  const dirty = JSON.stringify(f) !== JSON.stringify(data);
  const set = (patch: Partial<S>) => setF({ ...f, ...patch });
  const pct = Math.round(f.min_completeness_to_publish * 100);

  return (
    <>
      <section className="card">
        <h3><Building2 className="ic" />Organization</h3>
        <p className="hint">Shown in the header and on the sign-in page.</p>
        <div className="field" style={{ maxWidth: 420 }}><label htmlFor="org">Organization name</label><input id="org" value={f.org_name} maxLength={100} onChange={(e) => set({ org_name: e.target.value })} placeholder="e.g. ICP" /></div>
      </section>

      <section className="card">
        <h3><Bot className="ic" />What agents receive</h3>
        <p className="hint">Defaults applied when an application doesn't ask for something specific.</p>
        <div className="fields">
          <div>
            <div className="field"><label>Default language</label></div>
            <div className="radio-cards">
              <Choice value="en" current={f.default_lang} onPick={(v) => set({ default_lang: v })} title="English" text="Descriptions and names in English only." />
              <Choice value="ar" current={f.default_lang} onPick={(v) => set({ default_lang: v })} title="Arabic (English fallback)" text="Arabic where written, English where it isn't yet." />
              <Choice value="both" current={f.default_lang} onPick={(v) => set({ default_lang: v })} title="Both languages" text="English and Arabic side by side. Largest responses." />
            </div>
          </div>
          <div className="field" style={{ maxWidth: 320 }}>
            <label htmlFor="tok">Default size limit (tokens)</label>
            <input id="tok" type="number" min={0} max={200000} step={500} value={f.default_max_tokens} onChange={(e) => set({ default_max_tokens: Math.max(0, Number(e.target.value) || 0) })} />
            <div className="sub" style={{ marginTop: 3 }}>Long table descriptions are trimmed to fit. 0 means no limit unless the caller asks for one.</div>
          </div>
          <div>
            <div className="field"><label>Personal data (PII) columns</label></div>
            <div className="radio-cards">
              <Choice value="names_only" current={f.pii_columns_in_agent_output} onPick={(v) => set({ pii_columns_in_agent_output: v })} title="Show the column, hide its values" text="Agents know the column exists (so they can avoid it) but never see sample values." />
              <Choice value="exclude" current={f.pii_columns_in_agent_output} onPick={(v) => set({ pii_columns_in_agent_output: v })} title="Hide the column completely" text="PII columns are removed from everything agents see. Safest." />
            </div>
          </div>
        </div>
      </section>

      <section className="card">
        <h3><Rocket className="ic" />Publishing rules</h3>
        <p className="hint">Quality gates before a table becomes visible to agents. Applies to single, bulk and CSV publishing.</p>
        <div className="fields">
          <Switch checked={f.require_review_before_publish} onChange={(v) => set({ require_review_before_publish: v })} label="Require review before publishing" hint="A table must be marked “reviewed” first — a second pair of eyes before agents rely on it." />
          <div className="field" style={{ maxWidth: 420 }}>
            <label htmlFor="mc">Minimum documentation to publish: <b>{pct === 0 ? "no minimum" : `${pct}%`}</b></label>
            <input id="mc" type="range" min={0} max={100} step={5} value={pct} onChange={(e) => set({ min_completeness_to_publish: Number(e.target.value) / 100 })} style={{ padding: 0 }} />
            <div className="sub" style={{ marginTop: 3 }}>Share of the table's description, grain, type and column descriptions that must be filled in.</div>
          </div>
        </div>
      </section>

      <section className="card">
        <h3><EyeOff className="ic" />Reviewing changes</h3>
        <p className="hint">Edits to a published table are saved as pending changes and reviewed before agents see them. New columns, and columns with sensitive-looking names, are hidden until a steward releases them.</p>
        <div className="fields">
          <Switch checked={f.revision_requires_different_approver} onChange={(v) => set({ revision_requires_different_approver: v })} label="Require a second person to approve changes" hint="Whoever publishes a pending change must not be one of the people who edited it. Only turn this on if you have at least two stewards." />
          <div className="field">
            <label htmlFor="pat">Column names treated as sensitive</label>
            <textarea id="pat" rows={3} value={f.pii_name_patterns} onChange={(e) => set({ pii_name_patterns: e.target.value })} />
            <div className="sub" style={{ marginTop: 3 }}>Comma-separated words. A column whose name contains one (as a word, or at the start or end of a longer name) is quarantined when it first appears — for example <code>email</code> matches <code>customer_email</code> and <code>userEmail</code>, but not <code>lesson</code>.</div>
          </div>
        </div>
      </section>

      <section className="card">
        <h3><Lock className="ic" />Security</h3>
        <div className="field" style={{ maxWidth: 320 }}>
          <label htmlFor="sh">Stay signed in for (hours)</label>
          <input id="sh" type="number" min={1} max={720} value={f.session_hours} onChange={(e) => set({ session_hours: Math.min(720, Math.max(1, Number(e.target.value) || 1)) })} />
          <div className="sub" style={{ marginTop: 3 }}>Applies to new sign-ins.</div>
        </div>
      </section>

      <div className="savebar"><span className="muted">{dirty ? "You have unsaved changes" : "All settings saved"}</span><span style={{ flex: 1 }} />
        <button className="btn" disabled={!dirty} onClick={() => setF(data)}>Discard</button>
        <button className="btn primary" disabled={!dirty || save.isPending} onClick={() => save.mutate()}>{save.isPending ? "Saving…" : <><Check className="ic" />Save changes</>}</button>
      </div>
    </>
  );
}
