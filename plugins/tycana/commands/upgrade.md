---
description: "Check for plugin updates and upgrade to the latest version."
allowed-tools:
  - Bash
  - AskUserQuestion
---

# /tycana:upgrade — Plugin Update

Check for and install updates to the Tycana plugin.

## Process

1. **Get installed version.** Read from the plugin system's manifest:

   ```bash
   cat ~/.claude/plugins/installed_plugins.json
   ```

   Find `"tycana@tycana"` and extract the `version` and `gitCommitSha` fields.

2. **Fetch latest from GitHub.** Update the marketplace repo:

   ```bash
   claude plugin marketplace update tycana
   ```

3. **Read latest version from marketplace.** After the marketplace update:

   ```bash
   cat ~/.claude/plugins/marketplaces/tycana/plugins/tycana/.claude-plugin/plugin.json
   ```

   Extract the `version` field.

4. **Compare versions.**

   **If already on latest:**
   ```
   Tycana plugin is up to date (v1.0.1).
   ```
   Done.

   **If update available**, continue to step 5.

5. **Show what changed.** Read the changelog from the updated marketplace repo:

   ```bash
   cat ~/.claude/plugins/marketplaces/tycana/CHANGELOG.md
   ```

   Display only the entries between the installed and latest versions. Summarize concisely.

6. **Confirm with the user.** Show the update summary and ask:

   ```
   Tycana plugin update available: v1.0.0 → v1.0.1

   What's new:
   - Fixed date grounding in morning and review commands
   - Rewritten upgrade command

   Update now?
   ```

7. **Run the update.** Note: the CLI requires the fully qualified `plugin@marketplace` name.

   ```bash
   claude plugin update tycana@tycana
   ```

8. **Confirm success.**

   ```
   Tycana plugin updated to v1.0.1.
   Restart Claude Code to pick up the changes.
   ```

## If Marketplace Update Fails

"Couldn't check for updates — the marketplace repo may be unreachable. You can try manually:
1. `claude plugin marketplace update tycana`
2. `claude plugin update tycana@tycana`"
