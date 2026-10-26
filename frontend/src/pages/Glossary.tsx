import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, send } from "../api";
import { BookA, Plus, Trash2 } from "lucide-react";
import { useAuth } from "../auth";
import { EmptyState, Text, csv, useTitle, InfoTip } from "../ui";
import { HELP } from "../help";

const empty = { term: "", term_ar: "", definition: "", definition_ar: "", synonyms: [] as string[], synonyms_ar: [] as string[], links: [] as string[] };

export default function Glossary() {
  useTitle("Glossary");
  const qc = useQueryClient();
  const { canEdit } = useAuth();
  const { data } = useQuery({ queryKey: ["glossary"], queryFn: () => api<any[]>("/api/glossary") });
  const [f, setF] = useState<any>(empty);
  const refresh = () => qc.invalidateQueries({ queryKey: ["glossary"] });
  const add = useMutation({
    mutationFn: () => send("POST", "/api/glossary", { ...f, term_ar: f.term_ar || null, definition_ar: f.definition_ar || null }),
    onSuccess: () => { refresh(); setF(empty); },
  });
  const del = useMutation({ mutationFn: (id: number) => send("DELETE", `/api/glossary/${id}`), onSuccess: refresh });
  const t = (k: string, label: string, opts: { area?: boolean; rtl?: boolean } = {}) => (
    <Text key={`${k}-${data?.length}`} label={label} value={f[k] ?? ""} onSave={(v) => setF((x: any) => ({ ...x, [k]: v }))} {...opts} />
  );
  return (
    <div className="detail-wrap wide">
      <div className="d-kind"><BookA className="ic" />Vocabulary</div>
      <div className="d-title">Glossary <InfoTip help={HELP.glossary} /></div>
      <section className="card">
        <h3>Terms <span className="count-pill">{data?.length ?? 0}</span></h3>
        {data?.map((g) => (
          <div className="list-row" key={g.id}>
            <div className="lr-main">
              <div className="lr-title">{g.term}{g.term_ar && <span className="ar-text" dir="rtl" style={{ marginLeft: 10 }}>{g.term_ar}</span>}</div>
              <div>{g.definition}</div>
              {g.definition_ar && <div className="ar-text" dir="rtl">{g.definition_ar}</div>}
              <div className="chips">
                {[...(g.synonyms ?? []), ...(g.synonyms_ar ?? [])].map((s: string) => <span className="chip gold" key={s}>{s}</span>)}
                {(g.links ?? []).map((s: string) => <span className="chip" key={s}>{s}</span>)}
              </div>
            </div>
            {canEdit && <button className="btn danger" onClick={() => del.mutate(g.id)}><Trash2 className="ic" />Delete</button>}
          </div>
        ))}
        {data && !data.length && <EmptyState icon={BookA} title="No terms yet">Add the words people use, in English and Arabic, and what they mean in the data.</EmptyState>}
      </section>
      {canEdit && <section className="card">
        <h3>New term</h3>
        <div className="fields">
          <div className="two-col">{t("term", "Term · EN")}{t("term_ar", "المصطلح · عربي", { rtl: true })}</div>
          <div className="two-col">{t("definition", "Definition · EN", { area: true })}{t("definition_ar", "التعريف · عربي", { area: true, rtl: true })}</div>
          <div className="two-col">
            <Text label="Synonyms · EN (comma separated)" value={f.synonyms.join(", ")} onSave={(v) => setF({ ...f, synonyms: csv(v) })} />
            <Text rtl label="مرادفات · عربي" value={f.synonyms_ar.join("، ")} onSave={(v) => setF({ ...f, synonyms_ar: csv(v) })} />
          </div>
          <Text label="Links, e.g. table:lake.sales.fact_orders, column:lake.sales.fact_orders.net_amount" value={f.links.join(", ")} onSave={(v) => setF({ ...f, links: csv(v) })} />
        </div>
        <div style={{ marginTop: 14 }}><button className="btn primary" disabled={!f.term || !f.definition} onClick={() => add.mutate()}><Plus className="ic" />Add term</button></div>
        {add.error && <div className="banner bad">{String(add.error)}</div>}
      </section>}
    </div>
  );
}
