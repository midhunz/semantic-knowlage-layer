import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, errText, send } from "../../api";
import { AlertTriangle, Check, Cpu, Info as InfoIcon, Plug, ShieldAlert, Wrench } from "lucide-react";
import { Switch, useToast } from "../../ui";
import { Snippet } from "./shared";

type Tool = { name: string; summary: string; access: "catalog" | "raw" };
type Cfg = { mcp_enabled: boolean; mcp_disabled_tools: string[]; mcp_run_query_max_rows: number };
type McpInfo = { server: { name: string; transport: string; sdk_version: string; command: string }; tools: Tool[]; settings: Cfg };

const CLIENTS = [
  ["desktop", "Claude Desktop"],
  ["code", "Claude Code"],
  ["other", "Any MCP client"],
] as const;
type Client = (typeof CLIENTS)[number][0];

const store = (k: string, d: string) => { try { return localStorage.getItem(k) || d; } catch { return d; } };

export default function Mcp() {
  const qc = useQueryClient();
  const toast = useToast();
  const { data } = useQuery({ queryKey: ["mcp-info"], queryFn: () => api<McpInfo>("/api/admin/mcp") });
  const [f, setF] = useState<Cfg | null>(null);
  useEffect(() => { if (data) setF(data.settings); }, [data]);
  const [client, setClient] = useState<Client>("desktop");
  const [container, setContainer] = useState(() => store("sl.mcp.container", "semantic-layer-app-1"));
  const save = useMutation({
    mutationFn: () => send("PUT", "/api/admin/settings", f),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["mcp-info"] }); qc.invalidateQueries({ queryKey: ["settings"] }); toast("MCP settings saved"); },
    onError: (e) => toast(errText(e), true),
  });
  if (!data || !f) return <div className="loading">Loading…</div>;

  const dirty = JSON.stringify(f) !== JSON.stringify(data.settings);
  const set = (patch: Partial<Cfg>) => setF({ ...f, ...patch });
  const on = (t: Tool) => !f.mcp_disabled_tools.includes(t.name);
  const toggle = (t: Tool, v: boolean) => set({ mcp_disabled_tools: v ? f.mcp_disabled_tools.filter((x) => x !== t.name) : [...f.mcp_disabled_tools, t.name] });
  const enabledCount = data.tools.filter(on).length;
  const raw = data.tools.filter((t) => t.access === "raw");
  const rawOn = raw.filter(on).length > 0 && f.mcp_enabled;
  const name = container.trim() || "semantic-layer-app-1";
  const setName = (v: string) => { setContainer(v); try { localStorage.setItem("sl.mcp.container", v); } catch { /* ignore */ } };

  const args = ["exec", "-i", name, "python", "-m", "app.mcp_server"];
  const snippets: Record<Client, { title: string; code: string; note: string }[]> = {
    desktop: [{
      title: "claude_desktop_config.json",
      code: JSON.stringify({ mcpServers: { [data.server.name]: { command: "docker", args } } }, null, 2),
      note: "Add this under the existing \"mcpServers\" key (Settings → Developer → Edit Config), then restart Claude Desktop.",
    }],
    code: [{
      title: "Terminal",
      code: `claude mcp add ${data.server.name} -- docker ${args.join(" ")}`,
      note: "Run once on the machine where Claude Code is used. Check it with: claude mcp list",
    }],
    other: [
      { title: "Command to launch the server", code: `docker ${args.join(" ")}`, note: "Speaks MCP over standard input/output (stdio). Give this command to any client that supports local MCP servers." },
      { title: "Without Docker (from the backend folder)", code: `python -m app.mcp_server`, note: "Needs the same environment variables as the app (database URL). Use the same command and arguments in the client's config." },
    ],
  };

  return (
    <>
      <section className="card">
        <h3><Plug className="ic" />MCP connector</h3>
        <p className="hint">Lets AI assistants that support the Model Context Protocol read the published semantic layer: tables, metrics, dimensions and glossary.</p>
        <Switch checked={f.mcp_enabled} onChange={(v) => set({ mcp_enabled: v })} label="Allow MCP access"
          hint={f.mcp_enabled ? "Connected assistants can call the tools below." : "Every tool refuses calls until this is turned back on."} />
        <div className="chips" style={{ marginTop: 14 }}>
          <span className="chip">Server: {data.server.name}</span>
          <span className="chip">Transport: local ({data.server.transport})</span>
          <span className="chip">{enabledCount} of {data.tools.length} tools on</span>
          <span className="chip">SDK {data.server.sdk_version}</span>
        </div>
        <div className="banner" style={{ marginTop: 12 }}>
          <InfoIcon className="ic" />
          <span>This connector runs on the server and is started by the assistant's app with a command. It is <b>not a web address</b>, and there is no remote (HTTP) option yet.</span>
        </div>
      </section>

      <section className="card">
        <h3><Cpu className="ic" />Connect an assistant</h3>
        <p className="hint">Copy the configuration for your client. It starts the connector inside the running app container.</p>
        <div className="fields">
          <div className="field" style={{ maxWidth: 360 }}>
            <label htmlFor="mcp-container">App container name</label>
            <input id="mcp-container" value={container} spellCheck={false} onChange={(e) => setName(e.target.value)} />
            <div className="sub" style={{ marginTop: 3 }}>Find it with <code>docker ps</code>. Saved in this browser only.</div>
          </div>
          <div className="seg" role="tablist" aria-label="Client" style={{ justifySelf: "start" }}>
            {CLIENTS.map(([k, label]) => <button key={k} role="tab" aria-selected={client === k} className={client === k ? "on" : ""} onClick={() => setClient(k)}>{label}</button>)}
          </div>
          <div className="snips">
            {snippets[client].map((s) => (
              <div key={s.title}><Snippet title={s.title} code={s.code} /><div className="sub" style={{ marginTop: 6 }}>{s.note}</div></div>
            ))}
          </div>
        </div>
      </section>

      <section className="card">
        <h3><Wrench className="ic" />Tools assistants can call <span className="count-pill">{enabledCount}/{data.tools.length}</span></h3>
        <p className="hint">Switch off what you don't want assistants to use. A switched-off tool stays visible to the assistant but refuses every call, with a clear message. Changes apply to the next call.</p>
        <div className="grid-wrap" style={{ border: 0 }}>
          <table className="grid">
            <thead><tr><th style={{ width: 70 }}>On</th><th>Tool</th><th>What it does</th><th>Reads</th></tr></thead>
            <tbody>
              {data.tools.map((t) => (
                <tr key={t.name}>
                  <td>
                    <span className="switch"><input type="checkbox" role="switch" aria-label={`Allow ${t.name}`} checked={on(t)} onChange={(e) => toggle(t, e.target.checked)} /><i /></span>
                  </td>
                  <td><code>{t.name}</code></td>
                  <td>
                    {t.summary}
                    {t.name === "run_query" && (
                      <div className="mcp-limit">
                        <label htmlFor="mcp-rows">Max rows per call</label>
                        <input id="mcp-rows" type="number" min={1} max={1000} value={f.mcp_run_query_max_rows}
                          onChange={(e) => set({ mcp_run_query_max_rows: Math.min(1000, Math.max(1, Number(e.target.value) || 1)) })} />
                      </div>
                    )}
                  </td>
                  <td>{t.access === "raw"
                    ? <span className="chip warn with-ic"><AlertTriangle className="ic" />Raw data</span>
                    : <span className="chip ok with-ic"><Check className="ic" />Published catalog</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rawOn && (
          <div className="banner bad" style={{ marginTop: 12 }} role="alert">
            <ShieldAlert className="ic" />
            <span><b>{raw.map((t) => t.name).join(", ")}</b> runs read-only SQL straight on the data lake. It <b>ignores the publish and personal-data rules</b> and can read any column the lake account can see. Turn it off unless assistants truly need live data.</span>
          </div>
        )}
      </section>

      <section className="card">
        <h3><ShieldAlert className="ic" />Good to know</h3>
        <ul className="mcp-notes">
          <li><b>No sign-in.</b> Whoever can run the launch command can use every enabled tool. Control access to the server or container, not through API keys.</li>
          <li><b>No per-application limits.</b> API-key domain limits and scopes apply to the REST API, not to MCP.</li>
          <li><b>No usage log yet.</b> MCP calls are not recorded in the audit log.</li>
          <li>Need keys, domain limits and tracking? Use the REST API with an <Link to="/settings?tab=keys">API key</Link> instead (documentation at <code>/docs</code>).</li>
        </ul>
      </section>

      <div className="savebar"><span className="muted">{dirty ? "You have unsaved changes" : "All settings saved"}</span><span style={{ flex: 1 }} />
        <button className="btn" disabled={!dirty} onClick={() => setF(data.settings)}>Discard</button>
        <button className="btn primary" disabled={!dirty || save.isPending} onClick={() => save.mutate()}>{save.isPending ? "Saving…" : <><Check className="ic" />Save changes</>}</button>
      </div>
    </>
  );
}
