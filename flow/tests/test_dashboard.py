# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import frappe
from frappe.tests import IntegrationTestCase

from flow.api.dashboard import (
	RUN_ACTIVITY_CHART,
	TOKEN_TREND_CHART,
	get_run_metrics_chart,
	get_token_usage_coverage,
	get_token_usage_total,
)
from flow.flow.doctype.flow_run.flow_run import persist_result
from flow.lib.agent import RunResult
from flow.permissions import FLOW_USER_ROLE, ensure_flow_role


def _user(email: str, roles: list[str]) -> str:
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": email.split("@")[0],
				"send_welcome_email": 0,
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
	doc = frappe.get_doc("User", email)
	doc.set("roles", [])
	doc.save(ignore_permissions=True)
	if roles:
		doc.add_roles(*roles)
	return email


def _result(total_tokens: int, *, reported: bool) -> RunResult:
	prompt_tokens = total_tokens * 3 // 4
	completion_tokens = total_tokens - prompt_tokens
	return RunResult(
		output="done",
		messages=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "done"}],
		iterations=1,
		usage={
			"prompt_tokens": prompt_tokens,
			"completion_tokens": completion_tokens,
			"total_tokens": total_tokens,
		},
		usage_reported=reported,
	)


class TestFlowDashboardMetrics(IntegrationTestCase):
	def setUp(self):
		ensure_flow_role()
		model = frappe.get_doc(
			{
				"doctype": "Flow Model",
				"title": "Dashboard Test Model",
				"model_id": "openai/gpt-4o-mini",
				"enabled": 1,
			}
		).insert()
		self.agent = frappe.get_doc(
			{
				"doctype": "Flow Agent",
				"title": "Dashboard Test Agent",
				"model": model.name,
				"instructions": "Be terse.",
				"enabled": 1,
			}
		).insert()
		self.user = _user("flow-dashboard-owner@example.com", [FLOW_USER_ROLE])
		self.other_user = _user("flow-dashboard-other@example.com", [FLOW_USER_ROLE])

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _persist_for(self, user: str, result: RunResult) -> None:
		frappe.set_user(user)
		session = frappe.get_doc(
			{"doctype": "Flow Session", "agent": self.agent.name, "title": "dashboard test"}
		).insert(ignore_permissions=True)
		persist_result(result, source="Manual", input="hi", session=session.name)

	def test_metrics_respect_owner_permissions_and_report_coverage(self):
		self._persist_for(self.user, _result(8, reported=True))
		self._persist_for(self.user, _result(0, reported=False))
		self._persist_for(self.other_user, _result(20, reported=True))

		frappe.set_user(self.user)
		total = get_token_usage_total({"days": 30})
		coverage = get_token_usage_coverage({"days": 30})

		self.assertEqual(total["value"], 8)
		self.assertEqual(coverage["eligible_runs"], 2)
		self.assertEqual(coverage["reported_runs"], 1)
		self.assertEqual(coverage["value"], 50.0)

		activity = get_run_metrics_chart(RUN_ACTIVITY_CHART, timespan="Last Month", time_interval="Daily")
		token_trend = get_run_metrics_chart(TOKEN_TREND_CHART, timespan="Last Month", time_interval="Daily")
		self.assertEqual(sum(activity["datasets"][0]["values"]), 2)
		self.assertEqual(sum(token_trend["datasets"][0]["values"]), 8)

	def test_metrics_reject_users_without_flow_run_read_permission(self):
		frappe.set_user(_user("flow-dashboard-blocked@example.com", ["Desk User"]))

		with self.assertRaises(frappe.PermissionError):
			get_token_usage_total({"days": 30})
		with self.assertRaises(frappe.PermissionError):
			get_run_metrics_chart(RUN_ACTIVITY_CHART)

	def test_metrics_return_na_when_no_executed_runs_are_visible(self):
		frappe.set_user(self.user)

		coverage = get_token_usage_coverage({"days": 999})

		self.assertEqual(coverage["period_days"], 30)
		self.assertIsNone(coverage["value"])
		self.assertEqual(coverage["eligible_runs"], 0)

	def test_chart_endpoint_rejects_unknown_chart_and_incomplete_date_range(self):
		frappe.set_user(self.user)
		with self.assertRaises(frappe.ValidationError):
			get_run_metrics_chart("Any Other Chart")
		with self.assertRaises(frappe.ValidationError):
			get_run_metrics_chart(RUN_ACTIVITY_CHART, timespan="Select Date Range", from_date="2026-09-01")
