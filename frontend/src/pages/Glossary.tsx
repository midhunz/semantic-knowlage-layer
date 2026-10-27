import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, errText, send } from "../api";
import { BookA, Pencil, Plus, Trash2 } from "lucide-react";
import { useAuth } from "../auth";
import { EmptyState, StatusChip, Text, csv, useTitle, useToast, InfoTip } from "../ui";
import { ReviewBar } from "../review";
import { HELP } from "../help";

const empty = { term: "", term_ar: "", definition: "", definition_ar: "", synonyms: [] as string[], synonyms_ar: [] as string[], links: [] as string[] };

export default function Glossary() {
  useTitle("Glossary");
  const qc = useQueryClient();
  const toast = useToast();
  const { canEdit } = useAuth();
  const { data } = useQuery({ queryKey: ["glossary"], queryFn: () => api<any[]>("/api/glossary") });
  const [f, setF] = useState<any>(empty);
  const [editId, setEditId] = useState<number | null>(null);       // the draft being edited (null = adding a new term)
  const refresh = () => ["glossary", "review"].forEach((k) => qc.invalidateQueries({ queryKey: [k] }));
  const add = useMutation({
    mutationFn: () => {
      const body = { term: f.term, term_ar: f.term_ar || null, definition: f.definition, definition_ar: f.definition_ar || null, synonyms: f.synonyms, synonyms_ar: f.synonyms_ar, links: f.links };
      return editId ? send("PUT", `/api/glossary/${editId}`, body) : send("POST", "/api/glossary", body);
    },
    onSuccess: () => { refresh(); setF(empty); setEditId(null); toast(editId ? "Saved" : "Added as a draft"); },
    onError: (e) => toast(errText(e), true),
  });
  const startEdit = async (id: number) => { const g = await api<any>(`/api/glossary/${id}`); setF({ ...empty, ...g, term_ar: g.term_ar ?? "", definition_ar: g.definition_ar ?? "" }); setEditId(id); window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }); };
  const del = useMutation({ mutationFn: (id: number) => send("DELETE", `/api/glossary/${id}`), onSuccess: refresh });
  const t = (k: string, label: string, opts: { area?: boolean; rtl?: boolean } = {}) => (
    <Text key={`${k}-${data?.length}-${editId}`} label={label} value={f[k] ?? ""} onSave={(v) => setF((x: any) => ({ ...x, [k]: v }))} {...opts} />
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
              <div className="lr-title">{g.term}<span style={{ marginInlineStart: 8 }}><StatusChip status={g.status} /></span>{g.term_ar && <span className="ar-text" dir="rtl" style={{ marginLeft: 10 }}>{g.term_ar}</span>}</div>
              <div>{g.definition}</div>
              {g.definition_ar && <div className="ar-text" dir="rtl">{g.definition_ar}</div>}
              <div className="chips">
                {[...(g.synonyms ?? []), ...(g.synonyms_ar ?? [])].map((s: string) => <span className="chip gold" key={s}>{s}</span>)}
                {(g.links ?? []).map((s: string) => <span className="chip" key={s}>{s}</span>)}
              </div>
              <ReviewBar kind="glossary" item={g} name={g.term} onOpen={startEdit} />
            </div>
            {canEdit && g.status !== "published" && <button className="btn" onClick={() => startEdit(g.id)}><Pencil className="ic" />Edit</button>}
            {canEdit && <button className="btn danger" onClick={() => window.confirm(`Delete “${g.term}”${g.draft_id ? " and its draft" : ""}?`) && del.mutate(g.id)}><Trash2 className="ic" />Delete</button>}
          </div>
        ))}
        {data && !data.length && <EmptyState icon={BookA} title="No terms yet">Add the words people use, in English and Arabic, and what they mean in the data.</EmptyState>}
      </section>
      {canEdit && <section className="card">
        <h3>{editId ? "Edit draft" : "New term"}</h3>
        <div className="fields">
          <div className="two-col">{t("term", "Term · EN")}{t("term_ar", "المصطلح · عربي", { rtl: true })}</div>
          <div className="two-col">{t("definition", "Definition · EN", { area: true })}{t("definition_ar", "التعريف · عربي", { area: true, rtl: true })}</div>
          <div className="two-col">
            <Text label="Synonyms · EN (comma separated)" value={f.synonyms.join(", ")} onSave={(v) => setF({ ...f, synonyms: csv(v) })} />
            <Text rtl label="مرادفات · عربي" value={f.synonyms_ar.join("، ")} onSave={(v) => setF({ ...f, synonyms_ar: csv(v) })} />
          </div>
          <Text label="Links, e.g. table:lake.sales.fact_orders, column:lake.sales.fact_orders.net_amount" value={f.links.join(", ")} onSave={(v) => setF({ ...f, links: csv(v) })} />
        </div>
        <div style={{ marginTop: 14 }}><button className="btn primary" disabled={!f.term || !f.definition} onClick={() => add.mutate()}><Plus className="ic" />{editId ? "Save draft" : "Add term"}</button>{editId && <button className="btn" style={{ marginInlineStart: 8 }} onClick={() => { setF(empty); setEditId(null); }}>Cancel</button>}</div>
      </section>}
    </div>
  );
}
