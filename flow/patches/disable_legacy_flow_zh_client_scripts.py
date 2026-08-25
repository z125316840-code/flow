# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

"""Disable the site-local Flow Chinese UI scripts replaced by the bundled client."""

import frappe

LEGACY_SCRIPT_NAMES = (
	"ERP Flow Zh - Flow Agent",
	"ERP Flow Zh - Flow Knowledge Base",
	"ERP Flow Zh - Flow Knowledge Source",
	"ERP Flow Zh - Flow Model",
	"ERP Flow Zh - Flow Provider",
	"ERP Flow Zh - Flow Run",
	"ERP Flow Zh - Flow Session",
	"ERP Flow Zh - Flow Tool",
	"ERP Flow Zh - Flow Trigger",
)


def execute() -> None:
	enabled_scripts = frappe.get_all(
		"Client Script",
		filters={"name": ["in", LEGACY_SCRIPT_NAMES], "enabled": 1},
		pluck="name",
	)
	for name in enabled_scripts:
		frappe.db.set_value("Client Script", name, "enabled", 0, update_modified=False)
