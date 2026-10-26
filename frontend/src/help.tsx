import type { HelpContent } from "./ui";

/** One place for every page's help text, so the wording stays consistent and is easy to review or translate. */
export const HELP: Record<string, HelpContent> = {
  overview: {
    title: "Overview",
    lead: "Everything agents can use today, what needs your attention, and how complete the documentation is.",
    points: [
      <>The top row counts what is live for agents: tables, metrics, dimensions, glossary terms and documented columns.</>,
      <><b>Needs your attention</b> lists open work, most serious first. Click an item to go straight to it.</>,
      <>Coverage shows how much is documented in English and Arabic, least documented first, by domain, source or table type.</>,
      <>Insights, publishing status, recent activity and (for administrators) access summarize the rest.</>,
    ],
  },
  catalog: {
    title: "Catalog",
    lead: "Every table pulled from your data sources. Open a table to describe it, then publish it so agents can use it.",
    points: [
      <>Search covers tables, columns, descriptions and synonyms, in English and Arabic.</>,
      <>The quick filters are work lists: needs review, no description, no grain, no Arabic, unpublished.</>,
      <>Tick rows to set type, domain or owner, mark as reviewed, or publish in bulk.</>,
      <>Filters are kept in the address bar, so you can copy the link to share a view.</>,
    ],
    note: <>Agents only see <b>published</b> tables, and never see example values flagged as personal data.</>,
  },
  columns: {
    title: "Column dictionary",
    lead: "Describe a column name once and apply it to every table that has it.",
    points: [
      <>Columns are grouped by name across all sources and schemas.</>,
      <>Write the English and Arabic description once, then fill it into every matching column.</>,
      <>Choose to fill only the blanks, or to overwrite text that is already there.</>,
    ],
    note: <>When a name is used with different data types, check them before overwriting.</>,
  },
  changes: {
    title: "Pending changes",
    lead: "Edits to published tables wait here until a steward publishes them.",
    points: [
      <>Agents keep seeing the current version while edits are pending.</>,
      <>Review the differences, then publish them together as a new numbered version.</>,
      <>Every version is kept in the table's history and can be restored.</>,
    ],
  },
  quarantine: {
    title: "Quarantine",
    lead: "Columns held back from agents until someone has looked at them.",
    points: [
      <>New columns on tables that are already documented, and columns whose names look like personal data, land here automatically.</>,
      <>Release a column that is fine as it is.</>,
      <>Release a column holding personal data <i>as personal data</i>, so its values are masked (or hidden, as set in Settings).</>,
    ],
  },
  dimensions: {
    title: "Dimensions",
    lead: <>A way an answer can be broken down, such as <i>person category</i>, <i>emirate</i> or <i>gender</i>.</>,
    points: [
      <>Each dimension lists the values stored in the data, the words people use for them (English and Arabic), and who it applies to.</>,
      <>It is linked to the columns that hold it.</>,
      <>This is how an agent turns “residents” into the stored value <code>EXPAT</code>.</>,
    ],
  },
  sources: {
    title: "Sources",
    lead: "The data sources this catalog reads from. Each one is a Trino catalog.",
    points: [
      <>Sync pulls in tables and columns.</>,
      <>Your descriptions are never overwritten by a sync.</>,
      <>New or changed tables and columns land in the review queue.</>,
    ],
    note: <>Limiting a source to some schemas never touches tables in the others.</>,
  },
  metrics: {
    title: "Metrics",
    lead: "Governed business numbers that agents use exactly as written, instead of inventing their own SQL.",
    points: [
      <>Each metric has a definition, a calculation, a base table and the dimensions it can be broken down by.</>,
      <>New metrics are saved as drafts until you publish them.</>,
      <>Only <b>published</b> metrics are visible to agents. Drafts and reviewed metrics stay private.</>,
    ],
  },
  glossary: {
    title: "Glossary",
    lead: "The words people use, in English and Arabic, mapped to what they mean in the data.",
    points: [
      <>Agents resolve synonyms through this list.</>,
      <>Arabic matching ignores diacritics and alef / ya variants.</>,
    ],
  },
  settings: {
    title: "Settings",
    lead: "Organization-wide defaults and access control. Administrators only.",
    points: [
      <>General sets the organization name and what agents receive by default: language, size limit and how personal data is handled.</>,
      <>API keys, users, webhooks, the MCP connector and the audit log each have their own tab.</>,
    ],
  },
};
