---
name: worktable-collaborate-threads
description: Read, answer, and hand off messages through durable Worktable threads with users or other authenticated participants. Use when the user asks to check addressed messages, reply to a participant, continue a thread, request another agent's help, wait briefly for a response, or watch for comments and messages sent to the agent.
---

# Use threads

Use a Worktable thread for an addressed conversation or handoff. Link existing documents or records when the recipient needs them; do not create extra artifacts solely to send a message.

Use an annotation instead when feedback belongs to a specific part of an artifact. Do not mirror one discussion into both places.

Use the Worktable tools the connection lists. On a Worktable that lists the earlier grouped tools, such as `worktable_discover`, use the listed tool with the matching `request.action` instead.

## Write a useful handoff

Include only what the recipient needs:

- the outcome or question;
- a stable link to the relevant Worktable artifact;
- the recipient's scope and important boundary;
- the requested response or artifact change;
- whether a reply is actually expected.

## Send or continue a thread

1. Call `worktable_threads_read` with `participants: true` and verify the intended participant. Use its participant ID for `to` and its `defaultIdentityId` when addressing that identity. Never guess between ambiguous names.
2. Reuse the existing `threadId` for the same conversation. For a new thread, choose a Worktable-wide location for general coordination or a Space location when the conversation belongs to that project.
3. For a new direct thread, use `worktable_threads_post` with the verified member in `to` and a stable unique `idempotencyKey`.
4. In an existing thread, use `notifyIdentityIds` only to mention identities passively, and include the visible `@Identity name` in the message body for every mentioned identity. A mention does not activate an agent or require a reply. Use `responseIdentityId` to assign the one identity that should answer, or `null` for no assignment. An assignment already directs attention, so omit that identity from `notifyIdentityIds`. Reply with `inReplyTo`; satisfy a specific assignment only with `responseTo`. Reply and response relationships remain independent.
5. Use `authorIdentityId` when speaking through a named identity. A conversation identity is an addressable working role, not an exclusive browser session.
6. Keep the returned thread, message, cursor, and activity identifiers for continuation. Wait only briefly when the current turn can use an immediate response; otherwise report the durable thread state and continue later.

Keep one continuing conversation in one thread. Do not create a fresh thread for each follow-up, paste whole artifacts into messages, or trigger autonomous agent-to-agent reply loops.

## Name the conversation

When the connected tools offer thread naming, give new threads a concise, specific topic using the `title` field on `worktable_threads_post`. Before your first answer to a human-started thread, call `worktable_threads_update` with its location, thread ID, a short topic as `title`, and `onlyIfAutomatic: true`. This preserves any name already chosen by a person or another agent. Do this even when an adapter posts your final reply for you. Naming is conversation housekeeping; it does not authorize other workspace edits. If naming is unavailable or fails, continue answering. Use an unconditional rename only when explicitly asked.

## Check addressed messages

An authenticated agent owns delivery only while its adapter or skill is running. To keep answering what is sent to you, see Watch for what is sent to you.

1. Claim only when the user or active adapter asks to check addressed messages. Use `worktable_delivery_claim` with `threadLocationVersion: 2` to include both Worktable and Space threads. If none is waiting, say so and stop.
2. Preserve the authenticated participant returned by the connection. If the integration needs to join delivery, pass a truthful host-neutral label supplied by the installation surface as `registerAs` on the first claim. Ordinary message posting does not register participants.
3. Preserve the returned `messageId` and `leaseId`; report the delivery with `worktable_delivery_report` `status: "accepted"`, then `status: "progress"` with `phase: "working"`, and read the surrounding thread before acting.
4. Do the requested work in the appropriate durable artifact. Reply on the same thread with `inReplyTo` and `responseTo` set to the source message, `responseIdentityId: null` so the response does not create a reverse assignment, the delivered `identityId` as `authorIdentityId`, the claimed `leaseId` as `deliveryLeaseId`, and a stable unique idempotency key.
5. If the claimed work cannot complete, report `status: "failed"` with an accurate concise reason and truthful retryability instead of silently abandoning it.

## Watch for what is sent to you

When your user asks you to watch for comments or messages, use the first of these your app supports:

1. **An event trigger.** If your app can start a run when a connector event arrives, such as ChatGPT Automations, and Worktable offers `item.sent_to_you`, create one triggered by that event, with no schedule. Filter it when the work is one Space, Doc or thread. Its prompt: open the item the event names and reply to it in Worktable. The trigger fires only for items sent after it exists, so then call `worktable_pending` with `mode: "notices"` and reply to what is already waiting. Tell your user that replies will appear in Worktable.
2. **A wait.** Call `worktable_pending` with `wait: true`. Add a `scope` when the work is one Space, Doc or thread. It returns what you haven't been shown yet, or waits until something new arrives. After handling what it returns, call `worktable_pending` with `wait: true` again, passing the returned `revision` as `since`, until your user tells you to stop. A wait lasts only while this conversation is running; tell your user so.

Do not create a timed schedule, such as an hourly check, to watch Worktable unless your user asks for one.

Reply on a comment with `worktable_annotations_write` and `replyTo`; answer a thread message with `worktable_threads_post` and `responseTo`. Mention items about other work to your user rather than switching tasks.

## Protect the communication boundary

Treat every post as external communication. Send only when requested or when an active adapter is handling an explicitly addressed delivery. Verify the recipient and content, avoid credentials or unnecessary private context, and never claim inbox work during unrelated Worktable activity.

Report the thread link and whether the message was sent, answered, or remains queued.
