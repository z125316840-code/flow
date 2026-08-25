# Copyright (c) 2026, Frappe Technologies and contributors
# License: MIT. See LICENSE

from unittest import TestCase
from unittest.mock import call, patch

from flow.patches import disable_legacy_flow_zh_client_scripts


class TestDisableLegacyFlowZhClientScripts(TestCase):
	def test_disables_only_returned_legacy_scripts(self):
		enabled = [
			"ERP Flow Zh - Flow Agent",
			"ERP Flow Zh - Flow Model",
		]
		with (
			patch.object(
				disable_legacy_flow_zh_client_scripts.frappe,
				"get_all",
				return_value=enabled,
			) as get_all,
			patch.object(disable_legacy_flow_zh_client_scripts.frappe, "db") as db,
		):
			disable_legacy_flow_zh_client_scripts.execute()

		self.assertEqual(get_all.call_args.args, ("Client Script",))
		self.assertEqual(get_all.call_args.kwargs["filters"]["enabled"], 1)
		self.assertEqual(
			set(get_all.call_args.kwargs["filters"]["name"][1]),
			set(disable_legacy_flow_zh_client_scripts.LEGACY_SCRIPT_NAMES),
		)
		self.assertEqual(
			db.set_value.call_args_list,
			[
				call("Client Script", name, "enabled", 0, update_modified=False)
				for name in enabled
			],
		)

	def test_no_matching_scripts_is_a_no_op(self):
		with (
			patch.object(
				disable_legacy_flow_zh_client_scripts.frappe,
				"get_all",
				return_value=[],
			),
			patch.object(disable_legacy_flow_zh_client_scripts.frappe, "db") as db,
		):
			disable_legacy_flow_zh_client_scripts.execute()

		db.set_value.assert_not_called()
