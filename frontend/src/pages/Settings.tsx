import { Link, useSearchParams } from "react-router-dom";
import { History, KeyRound, Plug, ShieldCheck, SlidersHorizontal, Users as UsersIcon, Webhook } from "lucide-react";
import { EmptyState, useTitle, InfoTip } from "../ui";
import { HELP } from "../help";
import { useAuth } from "../auth";
import General from "./settings/General";
import ApiKeys from "./settings/ApiKeys";
import Users from "./settings/Users";
import Webhooks from "./settings/Webhooks";
import Mcp from "./settings/Mcp";
import Audit from "./settings/Audit";

const TABS = [
  ["general", "General", General, SlidersHorizontal],
  ["keys", "API keys", ApiKeys, KeyRound],
  ["users", "Users", Users, UsersIcon],
  ["webhooks", "Webhooks", Webhooks, Webhook],
  ["mcp", "MCP connector", Mcp, Plug],
  ["audit", "Audit log", Audit, History],
] as const;

export default function Settings() {
  const { isAdmin } = useAuth();
  const [sp, setSp] = useSearchParams();
  const tab = TABS.find((t) => t[0] === sp.get("tab")) ?? TABS[0];
  useTitle(`Settings · ${tab[1]}`);
  if (!isAdmin) {
    return <div style={{ paddingTop: 60 }}><EmptyState icon={ShieldCheck} title="Administrators only" actions={<Link className="btn" to="/">Back to overview</Link>}>Ask an administrator to change settings, or to give you a different role.</EmptyState></div>;
  }
  const Body = tab[2];
  return (
    <div>
      <div className="te-head">
        <div className="te-head-inner wide">
          <div className="d-kind"><ShieldCheck className="ic" />Administration</div>
          <div className="d-title">Settings <InfoTip help={HELP.settings} /></div>
          <div className="tabs" role="tablist" style={{ marginTop: 10 }}>
            {TABS.map(([k, label, , Icon]) => (
              <button key={k} role="tab" aria-selected={tab[0] === k} className={`tab${tab[0] === k ? " on" : ""}`} onClick={() => setSp(k === "general" ? {} : { tab: k })}><Icon className="ic" />{label}</button>
            ))}
          </div>
        </div>
      </div>
      <div className="te-body wide"><Body /></div>
    </div>
  );
}
