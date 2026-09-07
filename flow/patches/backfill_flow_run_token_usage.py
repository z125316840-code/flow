# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

"""Backfill dashboard-friendly token columns from the retained raw usage JSON."""

import frappe

from flow.flow.doctype.flow_run.flow_run import normalize_token_usage

BATCH_SIZE = 500


def execute() -> None:
	start = 0
	while True:
		runs = frappe.get_all(
			"Flow Run",
			fields=["name", "usage"],
			order_by="creation asc",
			start=start,
			page_length=BATCH_SIZE,
		)
		if not runs:
			break
		for run in runs:
			usage = normalize_token_usage(run.usage)
			# Historical code collapsed missing provider usage to zero. Mark only positive legacy
			# values as reported so the coverage card never overstates data completeness.
			frappe.db.set_value(
				"Flow Run",
				run.name,
				{
					**usage,
					"token_usage_reported": int(any(usage.values())),
				},
				update_modified=False,
			)
		start += len(runs)
