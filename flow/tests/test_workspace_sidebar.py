# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

import json
from pathlib import Path
from unittest import TestCase


class TestFlowWorkspaceSidebar(TestCase):
	def test_agent_memory_follows_run_in_conversations_section(self):
		sidebar_path = Path(__file__).parents[1] / "workspace_sidebar" / "flow.json"
		items = json.loads(sidebar_path.read_text())["items"]
		links = [item.get("link_to") for item in items]

		run_index = links.index("Flow Run")
		self.assertEqual(links[run_index + 1], "Flow Agent Memory")
		self.assertEqual(items[run_index + 1]["link_type"], "DocType")
		self.assertEqual(items[run_index + 1]["child"], 1)
