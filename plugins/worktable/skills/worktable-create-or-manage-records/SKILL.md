---
name: worktable-create-or-manage-records
description: Organize repeated structured information as durable Worktable Records. Use for research datasets, inventories, directories, pipelines, trackers, and other collections whose items need identity, fields, filtering, links, validation, or individual updates.
---

# Manage records

Use Records for items with their own identity and updates. A collection schema
defines the fields that people, agents, and HTML docs share.

Use the Worktable tools the connection lists. On a Worktable that lists the earlier grouped tools, such as `worktable_discover`, use the listed tool with the matching `request.action` instead.

## Choose Records

Use Records when people or agents will repeatedly create, update, compare, filter, sort, group, assign, or validate individual items. Keep a plan, decision, argument, or research synthesis in a Doc when its meaning lives in the whole. Use an HTML Doc only when a task-specific view materially improves work over the canonical Records.

## Model from the work

- Start with the questions, views, and state changes the collection must support. Make each field enable a current edit, validation rule, query, automation, or materially better scan.
- Usually use one collection for one real entity type. Give each Record a recognizable title or name and deduplicate by real-world identity before creating it.
- Use select fields for controlled states that drive workflow. Use relations when the target is another independently changing entity.
- Require only identity and workflow-critical fields. Keep long shared context in a Doc and item-specific context in a concise text field when it truly belongs there.
- Keep field keys stable and display names clear. Worktable owns creation and update provenance; do not recreate it as domain fields without a real need.

## Build safely

1. Discover related Docs and collections. Query likely matches before creating a collection or Record; reuse established names and identities.
2. Define the minimum viable schema before the first insert. For an ambiguous extraction, resolve material uncertainty about identity or scope before writing. Use a sample when it helps; do not interrupt an already authorized, well-defined import merely because it is large.
3. Evolve populated schemas additively. Carry forward existing fields, preserve compatible types, and resolve validation conflicts rather than bypassing them.
4. Write or update Records, then query them through the filters and ordering the real workflow uses. Verify count, identity, field values, relations, and expanded references where relevant.
5. Use the built-in table for generic inspection. Add an HTML view only when its controls or visual form materially improve the task.

## Preserve identity and data

Do not invent missing values, duplicate a collection under a near-synonymous name, or replace a relation with copied display text. Treat warnings as evidence: repair duplicate identities, unrecognizable titles, schema conflicts, and invalid references when the source supports a correction.

Do not delete records or remove schema fields as incidental cleanup. Permanent record deletion uses `worktable_delete` with `collectionId` and `recordId`, and needs an unambiguous target within the user's request. Removing a field from a schema does not purge its stored values. The result is complete when the collection remains understandable in the built-in table, contains no near-duplicate identities, and supports a real query or update without rereading the source transcript.
