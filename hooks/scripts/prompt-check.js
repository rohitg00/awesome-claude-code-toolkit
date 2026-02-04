const stdinData = [];
process.stdin.on("data", (chunk) => stdinData.push(chunk));
process.stdin.on("end", () => {
  const input = Buffer.concat(stdinData).toString().trim();
  let prompt = "";
  try {
    const parsed = JSON.parse(input);
    prompt = parsed.prompt || parsed.message || input;
  } catch (e) {
    prompt = input;
  }

  const words = prompt.split(/\s+/).filter(Boolean);
  const warnings = [];

  if (words.length < 3) {
    warnings.push("Very short prompt. Consider adding more context about what you want to achieve.");
  }

  const vagueWords = ["fix", "update", "change", "modify", "improve", "do"];
  if (words.length < 5 && vagueWords.some((w) => words.map((x) => x.toLowerCase()).includes(w))) {
    warnings.push("Prompt may be vague. Specify what to fix/update and where.");
  }

  if (prompt.includes("everything") || prompt.includes("all files")) {
    warnings.push("Broad scope detected. Consider narrowing to specific files or modules.");
  }

  console.log(JSON.stringify({ warnings, wordCount: words.length }));
});

if (process.stdin.isTTY) {
  console.log(JSON.stringify({ warnings: [], wordCount: 0 }));
}
