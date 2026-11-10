import { render, screen, fireEvent } from "@testing-library/react";
import { Button, IconButton, Seg, Switch } from "./components/ui/Button";
import { Logo } from "./components/ui/Chrome";
import { buildQuery, editBody, emptyFilters, COLS } from "./lib/model";
import { fmtPhone, safeUrl } from "./lib/format";

describe("Button system", () => {
  it("never submits by accident (type=button) and forwards clicks", () => {
    const fn = vi.fn();
    render(<Button onClick={fn}>Go</Button>);
    const b = screen.getByRole("button", { name: "Go" });
    expect(b).toHaveAttribute("type", "button");
    fireEvent.click(b); expect(fn).toHaveBeenCalledOnce();
  });
  it("loading disables the button and announces busy", () => {
    const fn = vi.fn();
    render(<Button loading onClick={fn}>Save</Button>);
    const b = screen.getByRole("button", { name: "Save" });
    expect(b).toBeDisabled(); expect(b).toHaveAttribute("aria-busy", "true");
    fireEvent.click(b); expect(fn).not.toHaveBeenCalled();
  });
  it("disabled buttons carry the not-allowed affordance classes", () => {
    render(<Button disabled>Nope</Button>);
    expect(screen.getByRole("button")).toHaveClass("disabled:cursor-not-allowed", "disabled:opacity-50");
  });
  it("every variant defines hover and active states", () => {
    for (const v of ["primary", "secondary", "band", "drawer"]) {
      const { unmount } = render(<Button variant={v}>{v}</Button>);
      const cls = screen.getByRole("button").className;
      expect(cls).toMatch(/hover:bg-/); expect(cls).toMatch(/active:/);
      unmount();
    }
  });
  it("IconButton exposes its label as the accessible name", () => {
    render(<IconButton label="Remove filter Dallas">×</IconButton>);
    expect(screen.getByRole("button", { name: "Remove filter Dallas" })).toBeInTheDocument();
  });
  it("Seg marks exactly the selected option as pressed", () => {
    const fn = vi.fn();
    render(<Seg label="View" value={3} onChange={fn} options={[[1, "1"], [3, "3"], [5, "5"]]} />);
    expect(screen.getByRole("button", { name: "3" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "1" })).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(screen.getByRole("button", { name: "5" })); expect(fn).toHaveBeenCalledWith(5);
  });
  it("Switch toggles with role=switch", () => {
    const fn = vi.fn();
    render(<Switch checked={false} onChange={fn} aria-label="Dark mode" />);
    fireEvent.click(screen.getByRole("switch", { name: "Dark mode" })); expect(fn).toHaveBeenCalledWith(true);
  });
});

describe("NTXP logo", () => {
  it("draws no substitute mark when the asset is missing — text alternative only", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    const { container } = render(<Logo />);
    fireEvent.error(container.querySelector("img"));
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toBe("NTXP LLC General Contractors");
    expect(container.querySelector(".sr-only")).not.toBeNull();
    expect(warn).toHaveBeenCalled();
  });
  it("uses the engine's reversed logo path with the standard 1.55in zone / 0.82in height", () => {
    const { container } = render(<Logo />);
    expect(container.querySelector("img")).toHaveAttribute("src", "/assets/ntxp_logo_reversed.png");
    expect(container.firstChild.className).toMatch(/w-\[1\.55in\]/); expect(container.firstChild.className).toMatch(/h-\[0\.82in\]/);
  });
});

describe("model helpers", () => {
  it("builds one query for table, CSV and reports (repeated keys = OR)", () => {
    const f = emptyFilters(); f.company = ["A", "B"];
    const q = new URLSearchParams(buildQuery({ f, q: "x", near: "Dallas, TX", miles: "25", sort: "name", dir: "asc" }, { limit: 5 }));
    expect(q.getAll("company")).toEqual(["A", "B"]); expect(q.get("near")).toBe("Dallas, TX"); expect(q.get("limit")).toBe("5");
  });
  it("proximity needs both near and miles", () => {
    expect(new URLSearchParams(buildQuery({ f: emptyFilters(), q: "", near: "Dallas", miles: "", sort: "name", dir: "asc" })).has("near")).toBe(false);
  });
  it("name edits split into first/last; other columns map to their field", () => {
    const name = COLS.find((c) => c.k === "name"), city = COLS.find((c) => c.k === "city");
    expect(editBody(name, "Ana Maria Ruiz")).toEqual({ first_name: "Ana Maria", last_name: "Ruiz" });
    expect(editBody(name, "Cher")).toEqual({ first_name: "", last_name: "Cher" });
    expect(editBody(city, "Waco")).toEqual({ city: "Waco" });
  });
  it("formats phones and rejects non-http URLs", () => {
    expect(fmtPhone("+12145551051")).toBe("214-555-1051");
    expect(safeUrl("javascript:alert(1)")).toBeNull(); expect(safeUrl("https://x.test")).toBe("https://x.test");
  });
});
