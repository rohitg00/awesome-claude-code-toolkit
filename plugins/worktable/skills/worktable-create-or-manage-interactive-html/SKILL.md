---
name: worktable-create-or-manage-interactive-html
description: Create or improve durable visual and interactive artifacts in Worktable. Use for dashboards, trackers, calculators, mini apps, slide presentations, and other requests that benefit from a polished HTML Doc.
---

# Build HTML

Use an HTML doc for an interactive tool, visual explanation, or custom view.
Keep it understandable when opened outside the current conversation.

Use the Worktable tools the connection lists. On a Worktable that lists the earlier grouped tools, such as `worktable_discover`, use the listed tool with the matching `request.action` instead.

## Choose the composition

- **Presentation or visual brief:** keep the complete high-level experience in one HTML Doc. Link a narrative Doc when deeper reasoning or source notes matter independently.
- **Board, tracker, planner, directory, or dashboard:** keep independently changing entities in Records; make the HTML Doc a focused view that subscribes to and updates those Records.
- **Calculator or mini tool:** keep deterministic logic in the HTML. Use `worktable.state` only for interface-local drafts, filters, selections, or preferences. Create Records only when outputs need durable identity or reuse.
- **Live external data:** request network access only when the user actually needs it. Prefer Worktable runtime APIs for Worktable data.

## Build the artifact

1. Discover the workspace and related artifacts. Update the existing HTML Doc when it already owns the job. A new HTML Doc needs a `lifetime`: `durable` for interfaces people will return to, `temporary` for a one-off view that only supports current work. Check a document's lifetime with `worktable_files_read`; change it later with `worktable_files_update` and `lifetime`.
2. Before updating an existing HTML Doc, read its complete source with `worktable_html_read` and `includeHtml: true`. List open annotations with `worktable_annotations_read` filtered by its `htmlId`, inspect the context of relevant instructions, and preserve user-owned content that the request does not replace.
3. Make the purpose and primary action clear. Use the content and task to choose the layout.
4. Read `worktable_guidance` with `topic: "html"` and the `runtime` profile for the authoritative sandbox, bridge, permission, and data contract. Do not treat visual workflow guidance as a server security boundary.
5. Model and seed canonical Records first when the interface depends on them. Then write one complete self-contained HTML document with the narrowest permissions that cover its actual calls.
6. Validate Mermaid sources with `worktable_mermaid` when embedding a diagram or returned SVG. Repair actionable Worktable validation warnings.
7. Inspect desktop/mobile and light/dark screenshots with `worktable_files_render` (or request a `preview` when you write the HTML). Read the image and diagnostics, then correct the source. Previews disable persistent writes and external network; `partial` identifies incomplete or blocked content. If a saved write's preview fails, retry `worktable_files_render`, not the write. Separately exercise important controls in the real interface and verify that intended Record mutations survive rereading the collection.

## Verify the result

- **Comprehension:** use descriptive headings and a clear next action. Remove controls, metrics, and decoration that do not help the task.
- **Visual craft:** refine typography, line length, spacing rhythm, alignment, contrast, and negative space. Use real content, responsive composition, and coherent light and dark themes through Worktable semantic variables.
- **Interaction:** give every control a purpose and legible loading, saving, success, empty, and failure states where relevant. Record-backed actions must update canonical Records, not only local HTML.
- **Accessibility:** use semantic headings and native controls, visible focus, keyboard operation, comfortable targets, reduced-motion support, and a non-drag path for drag-and-drop workflows.
- **Continuity:** explain the artifact without relying on the transcript, link supporting durable work, preserve user-owned content, and make the next update straightforward.

Return `urlToSendInChat` as the entry point and briefly name the durable sources behind the interface. The artifact is complete when its purpose is clear, its important path works with the intended data, and the user can return through one stable link.
