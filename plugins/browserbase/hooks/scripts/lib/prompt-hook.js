/**
 * prompt-hook.js — shared UserPromptSubmit boilerplate for the browserbase hooks.
 *
 * Reads the prompt text off stdin (plain text or the {prompt|message|user_prompt}
 * JSON shape Claude Code sends), passes it to `analyze(prompt)`, and — if it
 * returns a truthy string — emits the additionalContext hook payload.
 */

function run(analyze) {
  const chunks = [];
  process.stdin.on("data", (chunk) => chunks.push(chunk));
  process.stdin.on("end", () => {
    const input = Buffer.concat(chunks).toString().trim();
    let prompt = input;
    try {
      const parsed = JSON.parse(input);
      prompt = parsed.prompt || parsed.message || parsed.user_prompt || input;
    } catch {
      // not JSON — use the raw input as-is
    }

    const hint = analyze(prompt);
    if (hint) {
      console.log(
        JSON.stringify({
          hookSpecificOutput: {
            hookEventName: "UserPromptSubmit",
            additionalContext: hint,
          },
        })
      );
    }
  });

  if (process.stdin.isTTY) process.exit(0);
}

module.exports = { run };
