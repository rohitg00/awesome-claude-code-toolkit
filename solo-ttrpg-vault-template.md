# Solo TTRPG Vault Template

  A system- and setting-agnostic vault template for running solo tabletop RPGs with Claude Code as the GM.

  ## What it does

  A scaffolding kit for multi-month solo TTRPG campaigns where the LLM is the GM and the human is the player. Distilled from two real solo campaigns (Imperium Maledictum d100 and Cyberpunk RED d10). System- and setting-agnostic — you bring the system, PC, and setting; the
  template provides the structural conventions that make multi-month campaigns work.

  - **Slash commands**: `/play` (eager-load play context — character sheet, live state, rules quick-ref, tone docs, GM notes), `/roll` (Python-based dice with full Roll20 notation: Fudge, exploding, success-counting, keep-highest), `/oracle` (multi-system content randomness:
  axis, fate yes/no, tarot, runes, I Ching, prompt pairs)
  - **Six-file setup playbook** covering ~6–10 hours of campaign bringup (Setup Phases, Question Bank, Technical Patterns, Pitfalls and Lessons, Recurring Patterns)
  - **Scene Pacing Framework** — chunk taxonomy, ambient erosion, escalation ladder, per-chunk event checks; picks one of two resolution-engine patterns to match the system
  - **Tone framework** — Themes (content scope), Voice (prose register)
  - **GM Craft companion** — failure-handling spectrum (succeed-at-cost / fail-forward / hard fail), narrative authority handoff on critical successes, improv response spectrum (Yes-and / Yes-but / No-but / "you can certainly try")
  - **NPC scaffolds** — per-PC custom-tracker pattern, motivation-first NPC formula (want + distinctive marker + relationship memory + optional secret for antagonists), functionary templates
  - **MIGRATION.md** for forking older versions

  ## Quick start

  1. Click **Use this template** at https://github.com/Mirsellus/solo-ttrpg-vault-template or clone the repo
  2. Open Claude Code in the cloned directory; ask: *"I just cloned this, what is it and where do I start?"*
  3. Walk Stage 1 of `_README.md`: copy to a campaign directory, fix `.gitignore`, fill `CLAUDE.md` + `Setup Notes.md` with system / character / setting
  4. Walk Stages 2–7 (rulebooks → tone → character creation → slash commands → world bible → permissions)
  5. Run the Stage 8 readiness gates before session 1

  ## Links

  - **Repository**: https://github.com/Mirsellus/solo-ttrpg-vault-template
  - **License**: MIT

  ## Why use this

  Fills the empty quadrant in public Claude Code TTRPG tooling. Most existing public projects are d20-locked (built-in 5e rules), solo-without-GM (oracle-driven, no LLM-GM structure), or RAG-dependent. This one is system-agnostic, GM-with-human-player, and ships scaffolds rather
  than rules.

  Attribution: `scripts/oracle.py` and `scripts/dice.py` are MIT-licensed verbatim ports from [serelon/rpg-tools](https://github.com/serelon/rpg-tools) (headers and LICENSE preserved at `scripts/LICENSE-rpg-tools.txt`). `World Bible/GM Craft.md` paraphrases structure from
  [rjroy/adventure-engine-corvran](https://github.com/rjroy/adventure-engine-corvran)'s gm-craft skill (also MIT) — paraphrased rather than verbatim, with explicit attribution in the file's §5.
