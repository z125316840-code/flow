frappe.provide("frappe.dashboards.chart_sources");

frappe.dashboards.chart_sources["Flow Run Metrics"] = {
	method: "flow.api.dashboard.get_run_metrics_chart",
	filters: [],
};
