export const initials = (r) => ((r.first_name || "")[0] || "") + ((r.last_name || "")[0] || "");
export const mapUrl = (c, s) =>
  "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent([c, s].filter(Boolean).join(", "));
export function fmtPhone(p) {
  const d = String(p || "").replace(/\D/g, "").replace(/^1(\d{10})$/, "$1");
  return d.length === 10 ? d.slice(0, 3) + "-" + d.slice(3, 6) + "-" + d.slice(6) : p || "";
}
export const telHref = (p) => "tel:" + String(p).replace(/[^+\d]/g, "");
export const stamp = () => new Date().toISOString().slice(0, 10);
export const longDate = () => new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
export const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? u : null);
export function download(blob, name) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}
export const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode */ } },
};
