---
name: worktable-review-with-annotations
description: Create, inspect, reply to, update, or resolve situated Worktable annotations. Use when feedback belongs to a Doc section, block, text range, or HTML Doc, or when the user asks to address existing review feedback and coordinate a requested artifact edit.
---

# Review annotations

Use an annotation when requested feedback belongs beside an artifact. Reading an instruction annotation does not itself authorize acting on it. Use a thread for a broader conversation or handoff. When the user asks to address an instruction by changing its target, make the content change through the owning Doc or HTML workflow, then return to the annotation to preserve the review outcome.

Use the Worktable tools the connection lists. On a Worktable that lists the earlier grouped tools, such as `worktable_discover`, use the listed tool with the matching `request.action` instead.

## Anchor feedback precisely

1. Read the target artifact and list relevant open annotations before adding feedback. Avoid repeating an existing point.
2. Choose the narrowest stable target supported by the artifact:
   - `doc` for a whole Markdown Doc or whole rich Doc;
   - `block` for a section or block only when the Doc read returned persistent rich-block IDs; preserve its `blockId` and useful quote context;
   - `text` for a specific range only within a rich block with a known persistent `blockId`;
   - `html` with the required `htmlId` for an HTML Doc, which supports document-level annotation.
3. Use category `comment` for observation or discussion. Use `instruction` only for a requested change or constraint that should remain open until acted on.
4. Make the body actionable and self-contained. Include the concrete issue, why it matters, and the expected outcome without pasting the whole artifact.
5. Supply a stable `idempotencyKey` when retrying a create call could otherwise duplicate feedback.

## Continue or close review threads

- Use `worktable_annotations_read` with its `annotationId` and `includeTargetContext: true` before acting on an existing annotation. Check `targetExists` and `selectorMatch`; reread the artifact when the selector is fuzzy or stale.
- Reply when discussion or evidence belongs in the existing annotation thread. Do not create a second annotation for the same conversation.
- Update only annotation metadata or wording the user asked to change. For a requested content change, use the corresponding Doc or HTML workflow, verify the requested outcome, and then reply or resolve. Do not treat annotation status as proof that the underlying artifact changed.
- Resolve only after the instruction was addressed, superseded, or deliberately declined. Give a concise reason that preserves the decision.

## Preserve the review boundary

After creating or managing feedback, verify the annotation ID, category, status, target, and context. For annotation-only actions, confirm that the underlying Doc or HTML Doc is unchanged. For a requested artifact edit, verify the changed content and report both its path and the annotation action. Otherwise report no artifact path as changed.
