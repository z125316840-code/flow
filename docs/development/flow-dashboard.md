# Flow native dashboard

The Flow workspace uses Frappe's standard Workspace, Number Card, Dashboard Chart, and Dashboard
Chart Source records. It does not mount a separate frontend application or a Custom HTML Block.

## Metrics

- **Flow Agent Count**: count of `Flow Agent` documents visible to the current user.
- **Flow Knowledge Base Count**: count of `Flow Knowledge Base` documents visible to the current
  user. Users without read permission do not receive this Number Card from the workspace API.
- **Flow Token Usage 30 Days**: sum of `total_tokens` for visible, executed runs created during the
  rolling 30-day period and marked as having provider-reported usage.
- **Flow Token Coverage 30 Days**: percentage of visible, executed runs in the rolling 30-day period
  for which at least one model response supplied token usage. With no eligible runs, the card shows
  `N/A` instead of a misleading zero percent.
- **Flow Run Activity 30 Days**: visible runs with at least one model iteration, grouped by creation
  date.
- **Flow Token Trend 30 Days**: provider-reported `total_tokens`, grouped by creation date.

The chart time-grain and preset period remain adjustable through Frappe's native chart controls.

## Storage and migration

`Flow Run.usage` remains the raw cumulative JSON for compatibility and diagnostics. The hidden,
read-only `prompt_tokens`, `completion_tokens`, `total_tokens`, and `token_usage_reported` columns
are the query-friendly dashboard source. Counts are clamped to non-negative integers and total
tokens cannot be lower than the sum of prompt and completion tokens.
Both chat-completion token names (`prompt_tokens` and `completion_tokens`) and response-style names
(`input_tokens` and `output_tokens`) are normalized into these columns.

The post-model-sync patch backfills retained historical runs in batches of 500. Old code did not
preserve the difference between a missing usage payload and a reported zero, so historical rows
are marked covered only when their stored usage contains a positive count. Re-running the patch is
safe.

Flow Session log retention is configured for 90 days. This dashboard deliberately reports retained
operational history rather than promising permanent billing history. A future billing-grade view
should use a daily aggregate table that outlives session cleanup.

## Permission boundary

Number Cards and chart endpoints use `frappe.get_list`, so document permission query conditions and
owner-only restrictions apply. The two charts use a standard Frappe Dashboard Chart Source but call
an uncached Flow endpoint. This is intentional: Frappe's general Dashboard Chart cache is shared by
chart name, which is unsuitable for owner-specific Flow Run aggregates.

Required metric filters are rebuilt on the server. A client cannot remove the executed-run or
provider-usage conditions by changing request filters. Only the two exported Flow chart names are
accepted, and custom date ranges require both a start and end date.
