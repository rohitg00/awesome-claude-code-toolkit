import { Button } from "./ui/Button";

export function Gate({ message, onSignIn }) {
  return (
    <div className="gate fixed inset-0 z-[100] bg-band grid place-items-center p-4" id="gate">
      <div className="box bg-paper text-ink rounded-md p-7 max-w-[420px] w-full text-center shadow-[0_20px_60px_rgba(0,0,0,.5)]" role="dialog" aria-labelledby="gt">
        <h2 id="gt" className="m-0 mb-1.5 tracking-[.12em] uppercase text-navy dark:text-ink">NTXP Contacts</h2>
        <p className="mini text-xs text-ink-soft" id="gmsg">{message || "Sign in with your NTXP Google Workspace account to view the company contacts."}</p>
        <Button id="signin" variant="primary" className="w-full mt-3" onClick={onSignIn}>Sign in with Google · ntxpllc.com</Button>
      </div>
    </div>
  );
}

export function ExportRail({ onCsv, onPdf, onDrive }) {
  return (
    <div id="exports" className="exports fixed right-[max(12px,env(safe-area-inset-right,0px))] top-1/2 -translate-y-1/2 flex flex-col gap-2 z-30 max-[900px]:top-auto max-[900px]:bottom-0 max-[900px]:inset-x-0 max-[900px]:translate-y-0 max-[900px]:flex-row max-[900px]:justify-center max-[900px]:p-2 max-[900px]:bg-float max-[900px]:border-t max-[900px]:border-warm-edge">
      <Button id="xCsv" className="w-[148px] max-[900px]:w-auto max-[900px]:flex-1 bg-float shadow-[0_4px_14px_rgba(27,42,78,.2)] leading-tight" onClick={onCsv}>Export CSV</Button>
      <Button id="xPdf" className="w-[148px] max-[900px]:w-auto max-[900px]:flex-1 bg-float shadow-[0_4px_14px_rgba(27,42,78,.2)] leading-tight" onClick={onPdf}>Export PDF</Button>
      <Button id="xDrive" variant="primary" className="w-[148px] max-[900px]:w-auto max-[900px]:flex-1 shadow-[0_4px_14px_rgba(27,42,78,.2)] leading-tight" title="Saves the PDF into the project folder under !Active Projects in Google Drive" onClick={onDrive}>Save to project folder</Button>
    </div>
  );
}
