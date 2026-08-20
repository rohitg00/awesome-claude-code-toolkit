#!/usr/bin/env node
/**
 * announce-handoff.js  (PostToolUse: Bash, plugin-scoped)
 *
 * Fires after a Bash command. When that command was a real (non-dry-run)
 * project-intake build, it injects a short context note so the orchestrator picks
 * up the freshly written handoff.json and proceeds to the next step — making the
 * intake → orchestrator handoff automatic without the user typing the next command.
 *
 * It never blocks; it only adds context on a match, and stays silent otherwise.
 */

const stdinData = [];
process.stdin.on("data", (c) => stdinData.push(c));
process.stdin.on("end", () => {
  const raw = Buffer.concat(stdinData).toString().trim();
  let command = "";
  try {
    const p = JSON.parse(raw);
    command =
      (p.tool_input && (p.tool_input.command || p.tool_input.cmd)) ||
      p.command ||
      "";
  } catch (e) {
    command = raw;
  }

  // Require an actual python invocation of the builder — not a mention of the
  // file (e.g. `cat build_dossier.py`), which must NOT trigger a false handoff.
  const ran = /\bpython[0-9.]*\s+\S*build_dossier\.py\b/.test(command);
  const dryRun = /--dry-run\b/.test(command);
  if (!ran || dryRun) return; // not an intake build, or just a plan — stay silent

  console.log(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PostToolUse",
        additionalContext:
          "[project-intake] A project dossier build just ran. Read the " +
          "handoff.json it wrote under projects/<slug>/ (schema: " +
          "plugins/project-intake/schemas/handoff.schema.json). If status is " +
          "'ready_for_review' or 'partial', hand off to the " +
          "construction-doc-intelligence orchestrator and run the handoff's " +
          "next_step (default construction-doc-pipeline:review), routing each " +
          "extract to its domain skill. Surface anything in needs_human_review first.",
      },
    })
  );
});

if (process.stdin.isTTY) process.exit(0);
