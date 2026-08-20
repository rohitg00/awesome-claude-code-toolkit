# /paperclip-ai:toggle - Enable or disable the Paperclip AI connector

Toggle the Paperclip AI connector on or off. When disabled, all Paperclip hooks silently skip and MCP tools return a "disabled" message.

## Steps

1. Read the current state:
   ```bash
   cat ~/.paperclip/connector-state.json 2>/dev/null || echo "{}"
   ```
2. Check the current `enabled` field (defaults to `true` if absent)
3. Determine the new state:
   - If the user said "on", "enable", or "start": set `enabled` to `true`
   - If the user said "off", "disable", or "stop": set `enabled` to `false`
   - If no argument: flip the current value
4. Write the updated JSON back, preserving all other fields:
   ```bash
   node -e "
     const fs = require('fs');
     const f = require('os').homedir() + '/.paperclip/connector-state.json';
     let s = {};
     try { s = JSON.parse(fs.readFileSync(f, 'utf8')); } catch {}
     s.enabled = NEW_VALUE;
     fs.mkdirSync(require('path').dirname(f), { recursive: true });
     fs.writeFileSync(f, JSON.stringify(s, null, 2));
     console.log(JSON.stringify({ enabled: s.enabled }));
   "
   ```
5. Report the result clearly: "Paperclip connector is now **enabled**" or "**disabled**"
6. When enabling, check if Paperclip is running and suggest `npx paperclipai run` if not
7. When disabling, note that the change takes effect on the next session or tool call

## Rules

- Preserve all other fields in connector-state.json (agentKey, companyId, etc.)
- If connector-state.json doesn't exist yet, create it with the requested state
- The `enabled` field uses strict equality: absent = enabled, `false` = disabled
- This controls both hooks (auto-start, activity log, prompt enhance, session end) and MCP tools
