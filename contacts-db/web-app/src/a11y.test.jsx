import { render, screen, fireEvent } from "@testing-library/react";
import { useRef } from "react";
import { Toast } from "./components/ui/Chrome";
import { Gate } from "./components/Gate";
import { ContactsTable } from "./components/ContactsTable";
import { useInert, useFocusTrap } from "./lib/hooks";

describe("live regions", () => {
  it("toast is always mounted: polite status for info, assertive alert for errors", () => {
    const { rerender } = render(<Toast toast={null} />);
    expect(screen.getByRole("status")).toBeInTheDocument();
    rerender(<Toast toast={{ msg: "Saved", bad: false }} />);
    expect(screen.getByRole("status")).toHaveTextContent("Saved");
    rerender(<Toast toast={{ msg: "Nope", bad: true }} />);
    expect(screen.getByRole("alert")).toHaveAttribute("aria-live", "assertive");
  });
  it("toast pauses its timer on hover and focus (WCAG 2.2.1)", () => {
    const pause = vi.fn(), resume = vi.fn();
    render(<Toast toast={{ msg: "x" }} onPause={pause} onResume={resume} />);
    fireEvent.mouseEnter(screen.getByRole("status")); fireEvent.mouseLeave(screen.getByRole("status"));
    expect(pause).toHaveBeenCalled(); expect(resume).toHaveBeenCalled();
  });
});

describe("sign-in gate is a real modal", () => {
  it("is an alertdialog with aria-modal, announces its message and takes focus", () => {
    render(<Gate message="That account isn't allowed." onSignIn={() => {}} />);
    const d = screen.getByRole("alertdialog");
    expect(d).toHaveAttribute("aria-modal", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("isn't allowed");
    expect(screen.getByRole("button", { name: /sign in/i })).toHaveFocus();
  });
});

function Probe({ on }) {
  const ref = useRef(null);
  useInert(ref, on);
  useFocusTrap(ref, true);
  return <div><div data-testid="box" ref={ref}><button>a</button><button>b</button></div><button>outside</button></div>;
}
describe("focus helpers", () => {
  it("useInert sets the DOM property (React 18 ignores the attribute)", () => {
    const { rerender } = render(<Probe on />);
    expect(screen.getByTestId("box").inert).toBe(true);
    rerender(<Probe on={false} />);
    expect(screen.getByTestId("box").inert).toBe(false);
  });
  it("useFocusTrap wraps Tab at both ends", () => {
    render(<Probe on={false} />);
    const [a, b] = [screen.getByText("a"), screen.getByText("b")];
    b.focus(); fireEvent.keyDown(b, { key: "Tab" }); expect(a).toHaveFocus();
    a.focus(); fireEvent.keyDown(a, { key: "Tab", shiftKey: true }); expect(b).toHaveFocus();
  });
});

describe("label chips are mouse-clickable (was keyboard-only)", () => {
  const row = { id: 1, full_name: "A B", first_name: "A", last_name: "B", labels: ["DBE"] };
  const base = { rows: [row], total: 1, sort: "name", dir: "asc", onSort() {}, page: 0, size: 100, onPage() {}, error: "", onSaved() {}, onLabels() {}, toast() {} };
  it("click and Space both apply the filter", () => {
    const hot = vi.fn();
    render(<ContactsTable {...base} onHot={hot} />);
    const chip = screen.getByText("DBE");
    fireEvent.click(chip); expect(hot).toHaveBeenCalledWith("label", "DBE");
    fireEvent.keyDown(chip, { key: " " }); expect(hot).toHaveBeenCalledTimes(2);
    fireEvent.keyDown(chip, { key: "Enter" }); expect(hot).toHaveBeenCalledTimes(3);
  });
});
