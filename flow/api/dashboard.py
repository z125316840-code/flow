# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get_chart_config
from frappe.utils import add_days, cint, get_datetime, now_datetime

ALLOWED_PERIODS = frozenset({7, 30, 90})
DEFAULT_PERIOD = 30
RUN_ACTIVITY_CHART = "Flow Run Activity 30 Days"
TOKEN_TREND_CHART = "Flow Token Trend 30 Days"
ALLOWED_CHARTS = frozenset({RUN_ACTIVITY_CHART, TOKEN_TREND_CHART})
ALLOWED_TIMESPANS = frozenset({"Last Week", "Last Month", "Last Quarter", "Last Year", "Select Date Range"})
ALLOWED_TIME_INTERVALS = frozenset({"Daily", "Weekly", "Monthly", "Quarterly", "Yearly"})


@frappe.whitelist()
@frappe.read_only()
def get_token_usage_total(filters: str | dict[str, Any] | None = None) -> dict[str, Any]:
	"""Return visible token usage for the selected period as a native Number Card payload."""
	period, from_date = _period(filters)
	query_filters = _run_filters(from_date)
	query_filters.append(["Flow Run", "token_usage_reported", "=", 1])
	value = _aggregate_visible_runs("SUM", "total_tokens", query_filters)
	return {
		"value": value,
		"fieldtype": "Int",
		"route": ["List", "Flow Run"],
		"route_options": _route_options(from_date, reported_only=True),
		"period_days": period,
	}


@frappe.whitelist()
@frappe.read_only()
def get_token_usage_coverage(filters: str | dict[str, Any] | None = None) -> dict[str, Any]:
	"""Return the share of visible, executed runs for which a provider reported token usage."""
	period, from_date = _period(filters)
	eligible_filters = _run_filters(from_date)
	eligible = _aggregate_visible_runs("COUNT", "*", eligible_filters)
	reported_filters = [*eligible_filters, ["Flow Run", "token_usage_reported", "=", 1]]
	reported = _aggregate_visible_runs("COUNT", "*", reported_filters)
	value = round((reported / eligible) * 100, 1) if eligible else None
	return {
		"value": value,
		"fieldtype": "Percent",
		"route": ["List", "Flow Run"],
		"route_options": _route_options(from_date),
		"period_days": period,
		"reported_runs": reported,
		"eligible_runs": eligible,
	}


@frappe.whitelist()
@frappe.read_only()
def get_run_metrics_chart(
	chart_name: str,
	filters: str | list[Any] | dict[str, Any] | None = None,
	from_date: str | None = None,
	to_date: str | None = None,
	timespan: str | None = None,
	time_interval: str | None = None,
	**_kwargs: Any,
) -> dict[str, Any]:
	"""Return a native chart payload without Frappe's cross-user Dashboard Chart cache."""
	if chart_name not in ALLOWED_CHARTS:
		frappe.throw(_("Unsupported Flow dashboard chart."))

	chart = frappe.get_doc("Dashboard Chart", chart_name)
	frappe.has_permission("Dashboard Chart", ptype="read", doc=chart, throw=True)
	frappe.has_permission("Flow Run", ptype="read", throw=True)

	# Security and metric definitions stay server-side. Client-supplied filters must not be
	# able to remove the executed-run or token-coverage conditions.
	metric_filters: list[list[Any]] = [["Flow Run", "iterations", ">", 0]]
	if chart_name == TOKEN_TREND_CHART:
		metric_filters.append(["Flow Run", "token_usage_reported", "=", 1])
	metric_filters.append(["Flow Run", "docstatus", "<", 2])
	selected_timespan = timespan if timespan in ALLOWED_TIMESPANS else chart.timespan
	selected_interval = time_interval if time_interval in ALLOWED_TIME_INTERVALS else chart.time_interval
	if selected_timespan == "Select Date Range":
		if not from_date or not to_date:
			frappe.throw(_("A complete date range is required for this dashboard chart."))
		from_date = get_datetime(from_date)
		to_date = get_datetime(to_date)
	else:
		# Prevent stale, client-supplied range values from overriding the selected preset.
		from_date = None
		to_date = None

	return get_chart_config(
		chart,
		metric_filters,
		selected_timespan,
		selected_interval,
		from_date,
		to_date,
	)


def _period(filters: str | dict[str, Any] | None) -> tuple[int, Any]:
	filters = frappe.parse_json(filters) if isinstance(filters, str) else (filters or {})
	if not isinstance(filters, dict):
		frappe.throw(_("Dashboard filters must be an object."))
	period = cint(filters.get("days") or DEFAULT_PERIOD)
	if period not in ALLOWED_PERIODS:
		period = DEFAULT_PERIOD
	return period, add_days(now_datetime(), -period)


def _run_filters(from_date: Any) -> list[list[Any]]:
	frappe.has_permission("Flow Run", ptype="read", throw=True)
	return [
		["Flow Run", "creation", ">=", from_date],
		["Flow Run", "iterations", ">", 0],
	]


def _aggregate_visible_runs(function: str, fieldname: str, filters: list[list[Any]]) -> int:
	rows = frappe.get_list(
		"Flow Run",
		fields=[{function: fieldname, "as": "value"}],
		filters=filters,
		order_by=None,
	)
	return cint(rows[0].get("value")) if rows else 0


def _route_options(from_date: Any, *, reported_only: bool = False) -> dict[str, Any]:
	options: dict[str, Any] = {
		"creation": [">=", str(from_date)],
		"iterations": [">", 0],
	}
	if reported_only:
		options["token_usage_reported"] = ["=", 1]
	return options
