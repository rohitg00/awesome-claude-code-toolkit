export const FIELDS = [["company", "Company / Entity"], ["role", "Project Role"], ["trade", "Trade / Industry"], ["city", "City"], ["state", "State"], ["project", "Project"], ["label", "Labels"]];
export const emptyFilters = () => Object.fromEntries(FIELDS.map(([k]) => [k, []]));
export const COLS = [
  { k: "name", t: "Name", sort: "name", edit: "name" }, { k: "company", t: "Company / Entity", sort: "company", para: 1, edit: "company" },
  { k: "role", t: "Role", sort: "role", edit: "role" }, { k: "trade", t: "Trade", sort: "trade", edit: "trade" },
  { k: "city", t: "City", sort: "city", edit: "city" }, { k: "state", t: "State", sort: "state", edit: "state" },
  { k: "phone", t: "Phone #", sort: "phone", edit: "phone" }, { k: "email", t: "Email", sort: "email", edit: "email" },
  { k: "labels", t: "Labels", para: 1 }, { k: "linkedin", t: "LinkedIn", edit: "linkedin_url" },
  { k: "project", t: "Project", sort: "project", edit: "project" },
];
export const REPORTS = [["directory", "Project Directory"], ["full", "Full Contact Directory"], ["trade", "Subcontractors by Trade"], ["company", "Company / Entity Rollup"], ["label", "Group / Label Rollup"]];
export const PALETTES = [["ntxp", "NTXP Standard", "#1B2A4E"], ["field", "Field (copier-safe)", "#E4DCD0"], ["slate", "Slate", "#2B3A55"], ["graphite", "Graphite", "#2A2F36"]];

/** Query string shared by the table, CSV, report preview and render endpoints. */
export function buildQuery(s, extra = {}) {
  const p = new URLSearchParams();
  for (const [k] of FIELDS) s.f[k].forEach((v) => p.append(k, v));
  if (s.q) p.set("q", s.q);
  if (s.near && s.miles) { p.set("near", s.near); p.set("miles", s.miles); }
  p.set("sort", s.sort); p.set("dir", s.dir);
  for (const k in extra) p.set(k, extra[k]);
  return p.toString();
}

/** A name edit becomes first/last; everything else maps to one field. */
export function editBody(col, val) {
  if (col.k !== "name") return { [col.edit]: val };
  const parts = val.split(/\s+/).filter(Boolean);
  if (parts.length <= 1) return { first_name: "", last_name: parts[0] || "" };   // one word = a last name
  const last = parts.pop();
  return { first_name: parts.join(" "), last_name: last };
}

export const rawFor = (c, r) => (c.k === "name" ? r.full_name || "" : c.k === "linkedin" ? r.linkedin_url || "" : r[c.k] || "");
