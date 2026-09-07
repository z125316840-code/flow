# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import json
from pathlib import Path
from unittest import TestCase

FLOW_MODULE = Path(__file__).parents[1] / "flow"

NUMBER_CARDS = {
	"Flow Agent Count": "flow_agent_count",
	"Flow Knowledge Base Count": "flow_knowledge_base_count",
	"Flow Token Usage 30 Days": "flow_token_usage_30_days",
	"Flow Token Coverage 30 Days": "flow_token_coverage_30_days",
}

DASHBOARD_CHARTS = {
	"Flow Run Activity 30 Days": "flow_run_activity_30_days",
	"Flow Token Trend 30 Days": "flow_token_trend_30_days",
}


def _load_export(kind: str, slug: str) -> dict:
	path = FLOW_MODULE / kind / slug / f"{slug}.json"
	return json.loads(path.read_text())


class TestFlowWorkspaceDashboard(TestCase):
	def setUp(self):
		path = FLOW_MODULE / "workspace" / "flow" / "flow.json"
		self.workspace = json.loads(path.read_text())
		self.blocks = json.loads(self.workspace["content"])

	def test_workspace_uses_only_native_dashboard_blocks(self):
		self.assertEqual(self.workspace["custom_blocks"], [])
		self.assertEqual(
			{row["number_card_name"] for row in self.workspace["number_cards"]},
			set(NUMBER_CARDS),
		)
		self.assertEqual(
			{row["chart_name"] for row in self.workspace["charts"]},
			set(DASHBOARD_CHARTS),
		)
		self.assertEqual(len({block["id"] for block in self.blocks}), len(self.blocks))
		self.assertTrue(
			all(
				block["type"] in {"header", "number_card", "chart", "shortcut", "card"}
				for block in self.blocks
			)
		)

	def test_workspace_places_four_metrics_before_two_charts(self):
		metric_blocks = [block for block in self.blocks if block["type"] == "number_card"]
		chart_blocks = [block for block in self.blocks if block["type"] == "chart"]

		self.assertEqual([block["data"]["col"] for block in metric_blocks], [3, 3, 3, 3])
		self.assertEqual([block["data"]["col"] for block in chart_blocks], [6, 6])
		self.assertLess(self.blocks.index(metric_blocks[-1]), self.blocks.index(chart_blocks[0]))

	def test_number_cards_are_standard_permission_aware_records(self):
		cards = {name: _load_export("number_card", slug) for name, slug in NUMBER_CARDS.items()}
		for name, card in cards.items():
			self.assertEqual(card["name"], name)
			self.assertEqual(card["module"], "Flow")
			self.assertTrue(card["is_standard"])
			self.assertTrue(card["is_public"])

		self.assertEqual(cards["Flow Agent Count"]["document_type"], "Flow Agent")
		self.assertEqual(cards["Flow Agent Count"]["function"], "Count")
		self.assertEqual(cards["Flow Knowledge Base Count"]["document_type"], "Flow Knowledge Base")
		self.assertEqual(cards["Flow Knowledge Base Count"]["function"], "Count")
		for name in ("Flow Token Usage 30 Days", "Flow Token Coverage 30 Days"):
			self.assertEqual(cards[name]["type"], "Custom")
			self.assertEqual(cards[name]["document_type"], "Flow Run")
			self.assertEqual(json.loads(cards[name]["filters_json"]), {"days": "30"})

	def test_charts_use_native_flow_run_aggregates(self):
		charts = {name: _load_export("dashboard_chart", slug) for name, slug in DASHBOARD_CHARTS.items()}
		for name, chart in charts.items():
			self.assertEqual(chart["name"], name)
			self.assertEqual(chart["module"], "Flow")
			self.assertEqual(chart["chart_type"], "Custom")
			self.assertEqual(chart["source"], "Flow Run Metrics")
			self.assertEqual(chart["roles"], [{"role": "Flow User"}])
			self.assertEqual(chart["document_type"], "Flow Run")
			self.assertEqual(chart["based_on"], "creation")
			self.assertEqual(chart["time_interval"], "Daily")
			self.assertEqual(chart["timespan"], "Last Month")

		self.assertEqual(charts["Flow Run Activity 30 Days"]["type"], "Bar")
		self.assertEqual(
			json.loads(charts["Flow Run Activity 30 Days"]["filters_json"]),
			[["Flow Run", "iterations", ">", 0]],
		)
		self.assertEqual(charts["Flow Token Trend 30 Days"]["value_based_on"], "total_tokens")
		self.assertEqual(
			json.loads(charts["Flow Token Trend 30 Days"]["filters_json"]),
			[
				["Flow Run", "iterations", ">", 0],
				["Flow Run", "token_usage_reported", "=", 1],
			],
		)

	def test_custom_chart_source_calls_permission_aware_uncached_endpoint(self):
		source = _load_export("dashboard_chart_source", "flow_run_metrics")
		self.assertEqual(source["name"], "Flow Run Metrics")
		self.assertTrue(source["timeseries"])

		config_path = FLOW_MODULE / "dashboard_chart_source" / "flow_run_metrics" / "flow_run_metrics.js"
		config = config_path.read_text()
		self.assertIn('frappe.dashboards.chart_sources["Flow Run Metrics"]', config)
		self.assertIn('method: "flow.api.dashboard.get_run_metrics_chart"', config)
