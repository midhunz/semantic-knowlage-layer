# Dimensions

A **dimension** is a way answers can be broken down — *person category*, *emirate*, *gender*. It is a **business concept**, separate from any one table: the same dimension can live in the columns of several fact tables. Agents use it to turn what a person says (“residents”) into what is stored (`EXPAT`), and to know who a breakdown applies to.

Sidebar → **Dimensions**. Each dimension has five tabs:

| Tab | What you author |
|---|---|
| **Meaning** | Label and description in English and Arabic ("what it means" — the planner reads this to decide when the dimension applies; state scope rules in plain words), plus synonyms that name the dimension itself. |
| **Values** | The vocabulary. Each row: the **stored value** exactly as in the data, English and Arabic labels, and the **words people use** (aliases, either language, typed as tags). The stored value cannot be renamed — other rules refer to it. |
| **Families** | One business word that stands for several values ("gulf residents" = `GCC` + `EXPAT`). Needs at least two values. |
| **Applies to** | Who the dimension applies to: *Everyone*, or *Only where <another dimension> is one of …* (e.g. tribes → citizens only), with an optional note in each language. Shown to agents as an explicit instruction; **the application does not run any query**. |
| **Used in** | The physical columns that hold this dimension, across tables. A column belongs to one dimension. |

## Load values from the data
**Values → Load values from the data** reads the real distinct values of the linked columns from the lake (most frequent first, up to 200, from a sample of the table). Nothing is saved until you tick what to add. Columns marked **PII**, **hidden for review**, or dropped from the lake are **never read**; an unreachable lake is reported, not fatal. It also lists vocabulary values that were not seen in the data.

## Validation
* Families and "applies to" rules must point at **listed values** (and existing dimensions). Invalid ones are rejected when saved, and a dimension with errors cannot be published.
* **Removing a value** shows what depends on it. Its aliases go with it; it is taken out of families (a family left with one value is dropped). A value used by another dimension's **"applies to"** rule **cannot** be removed until that rule is changed — those rules change reported numbers.
* Warnings (not blocking): a word that can mean more than one value, circular restrictions, linked columns dropped from the lake.

## What agents get
Only **published** dimensions are visible (and, for a domain-restricted API key, only those linked to a column in its domains).

* `GET /agent/resolve-value?text=residents[&dimension=…][&lang=…]` — also MCP `resolve_value`. Returns matches `{dimension, value, label, via}` where `via` is `value`, `label`, `alias` or `family`, plus `ambiguous` and any dimension the word *names*. Matching ignores case, Arabic diacritics and letter variants (أ/ا, ة/ه…), spacing and edge punctuation.
* `GET /agent/dimensions` (summaries), `GET /agent/dimensions/{key}` — also MCP `list_dimensions`, `describe_dimension`: meaning, every value with labels and aliases, families, the "applies to" instruction (structured conditions plus a sentence in English/Arabic), and the live columns that hold it.
* `GET /agent/dimensions?full=true&format=yaml|json` — every dimension as one document.
* A **table's context** names the dimension on each linked column (`dimension: person_category`) and adds a compact `dimensions:` block (stored values with labels, capped at 30 with a pointer to `resolve_value`, and the "applies to" instruction). Aliases stay out of table contexts to save tokens.

`lang=en|ar|both` works everywhere, with the admin default when omitted.

## Notes and limits
Dimension edits are **live** (not staged like published tables) and recorded in the audit log; a `dimension.updated` webhook fires when a published one changes. Not included yet: planner-behaviour rules (one name = one value; what to do with a value the user did not say), and a "used by" view linking dimensions to metrics.
