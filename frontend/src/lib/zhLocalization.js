const MARKER = "__erp_flow_zh_ui_v3";

const isChinese = () => {
	const language = frappe.boot?.lang || document.documentElement.lang || "";
	return language.toLowerCase().startsWith("zh");
};

const isFlowRoute = () => /^\/(desk|app)\/flow(?:[-/]|$)/.test(window.location.pathname);

export function installFlowZhLocalization() {
	if (!isChinese()) return;

	const exactSources = [
		"List View",
		"Default Layout",
		"Enabled",
		"Filter",
		"Clear all filters",
		"Created On",
		"Title",
		"Status",
		"Full screen",
		"Close (Ctrl+I)",
		"Send",
		"Default",
		"Begin typing for results.",
		"descending",
		"Select All",
		"Menu",
	];
	const exact = new Map(exactSources.map((source) => [source, __(source)]));
	const sidebar = new Map(
		["desk", "app"].flatMap((prefix) => [
			[`/${prefix}/flow`, __("Flow")],
			[`/${prefix}/flow-model`, __("Flow Model")],
			[`/${prefix}/flow-tool`, __("Flow Tool")],
			[`/${prefix}/flow-run`, __("Flow Run")],
		])
	);

	const replaceTextNode = (node) => {
		const raw = node.nodeValue || "";
		const value = raw.trim();
		if (!value) return;

		let translated = exact.get(value);
		if (!translated && value === `Add ${__("Flow Agent")}`) {
			translated = __("Add Flow Agent");
		}
		if (translated && translated !== value) {
			node.nodeValue = raw.replace(value, translated);
		}
	};

	const translateElement = (element) => {
		for (const attr of ["aria-label", "title", "placeholder"]) {
			const value = element.getAttribute?.(attr);
			if (value && exact.has(value)) element.setAttribute(attr, exact.get(value));
			if (value === "Ask Flow…") element.setAttribute(attr, __("Ask Flow…"));
		}

		const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
		const nodes = [];
		while (walker.nextNode()) nodes.push(walker.currentNode);
		nodes.forEach(replaceTextNode);
	};

	const apply = () => {
		if (!isFlowRoute()) return;

		document
			.querySelectorAll(
				"button, label, [role='columnheader'], [role='status'], .list-row-head, .filter-selector, .sort-selector, .page-actions, .page-actions *, .standard-filter-section, .standard-filter-section *, input, textarea"
			)
			.forEach(translateElement);

		for (const anchor of document.querySelectorAll("a[href]")) {
			const path = new URL(anchor.href, window.location.origin).pathname;
			const translated = sidebar.get(path);
			if (!translated) continue;

			const candidates = [...anchor.querySelectorAll("span, div")].filter(
				(node) => node.children.length === 0 && node.textContent.trim()
			);
			const target = candidates.at(-1);
			if (target) target.textContent = translated;
			else if (anchor.children.length === 0) anchor.textContent = translated;
			anchor.setAttribute("aria-label", translated);
			anchor.setAttribute("title", translated);
		}

		for (const element of document.querySelectorAll(
			"[aria-label='Ask Flow…'], [placeholder='Ask Flow…']"
		)) {
			element.setAttribute("aria-label", __("Ask Flow…"));
			element.setAttribute("placeholder", __("Ask Flow…"));
		}
	};

	if (window[MARKER]?.observer) {
		window[MARKER].apply = apply;
		apply();
		return;
	}

	let scheduled = false;
	const observer = new MutationObserver(() => {
		if (scheduled) return;
		scheduled = true;
		requestAnimationFrame(() => {
			scheduled = false;
			apply();
		});
	});
	observer.observe(document.body, { childList: true, subtree: true });
	window[MARKER] = { observer, apply };
	apply();
}
