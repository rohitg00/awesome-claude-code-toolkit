# Tycana Tool Reference

Quick parameter reference for all 14 Tycana MCP tools. Use this when you need exact parameter names and values.

## Capture & Update

### `capture` — Create a new item
| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| title | string | yes | 1-500 chars |
| body | string | no | Detailed description |
| effort | string | no | `quick`, `small`, `medium`, `large` |
| energy | string | no | `deep`, `routine` |
| project | string | no | Project name (max 200 chars) |
| due | datetime | no | ISO 8601 |
| provenance | object | no | `{source, trigger, reference}` |

### `update_item` — Modify an existing item
| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| item_id | string | yes | UUID |
| title | string | no | New title |
| body | string | no | New description |
| effort | string | no | `quick`, `small`, `medium`, `large` |
| energy | string | no | `deep`, `routine` |
| project | string | no | New project name |
| due | datetime | no | New due date |
| clear_fields | list | no | Fields to clear: `body`, `effort`, `energy`, `project`, `due` |

### `complete` — Mark item done
| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| item_id | string | yes | UUID |
| outcome | string | yes | `resolved`, `wont_do`, `delegated`, `deferred` |
| notes | string | no | What happened or why |
| follow_up_title | string | no | Creates a follow-up item |
| follow_up_body | string | no | Body for the follow-up |

Returns: completed item, follow-up (if created), newly unblocked items, project cleanup signal.

### `delete_item` — Permanently remove an item
| Parameter | Type | Required |
|-----------|------|----------|
| item_id | string | yes |

## Retrieval

### `get_context` — Situational briefing
| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| scope | string | `today` | `today`, `this_week`, `full`, `project:{name}` |

Returns: urgency groups, recent completions, personal context, projects, workload, stale items, velocity, intelligence signals. Sections expand with scope.

### `search` — Full-text search
| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| query | string | — | Supports `OR`, `-negation`, `"quoted phrases"` |
| project | string | — | Filter by project |
| status | string | `active` | `active`, `completed`, `all` |
| limit | int | 20 | 1-50 |

### `list_items` — Browse with filters
| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| status | string | `active` | `active`, `completed`, `all` |
| project | string | — | Filter by project (use `unassigned` for no project) |
| outcome | string | — | `resolved`, `wont_do`, `delegated`, `deferred` |
| created_after | string | — | ISO 8601 date |
| created_before | string | — | ISO 8601 date |
| completed_after | string | — | ISO 8601 date |
| completed_before | string | — | ISO 8601 date |
| sort | string | `created` | `created`, `updated`, `due`, `completed` |
| limit | int | 20 | 1-50 |
| offset | int | 0 | Pagination |

### `get_item` — Full item detail
| Parameter | Type | Required |
|-----------|------|----------|
| item_id | string | yes |

Returns: all fields including body, provenance, and incoming/outgoing relationships.

## Planning & Intelligence

### `plan_day` — Daily plan
| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| available_hours | float | 8.0 | Hours available |
| energy_preference | string | `start_deep` | `start_deep`, `start_easy` |
| project | string | — | Optional project filter |

Returns: ordered plan with time estimates, priority scores, excluded items with reasons.

### `what_next` — Top 3 recommendations
| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| available_time | string | `hour` | `quick` (15min), `hour` (~60min), `deep` (2+hrs) |
| energy | string | `deep` | `deep`, `routine` |

Returns: scored recommendations with reasoning and what each unblocks.

### `review` — Progress assessment
| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| scope | string | `this_week` | `today`, `this_week`, `this_month`, `project:{name}` |
| focus | string | `full` | `progress`, `health`, `patterns`, `full` |

Returns: metrics, health assessment, velocity trends, completion patterns, slip rate, growth trend, narrative cues. Sections expand with focus level.

## Relationships & Memory

### `relate_items` — Connect items
| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| source_id | string | yes | UUID |
| target_id | string | yes | UUID |
| rel_type | string | yes | `blocking` (source blocks target), `related_to`, `follows_up`, `spawned_from` |

### `remember` — Store personal context
| Parameter | Type | Default | Values |
|-----------|------|---------|--------|
| fact | string | — | 1-1000 chars |
| category | string | `note` | `preference`, `context`, `goal`, `constraint`, `note` |

Max 50 facts per user. Retrieve via `get_context` (personal_context section).

## Project Management

### `cleanup_project` — Bulk project operations
| Parameter | Type | Required | Values |
|-----------|------|----------|--------|
| project | string | yes | Project name |
| action | string | yes | `preview`, `complete_all`, `delete_all` |
| confirm | bool | no | Must be `true` for bulk operations |
