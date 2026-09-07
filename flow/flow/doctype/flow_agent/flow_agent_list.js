// Copyright (c) 2026, Frappe Technologies and contributors
// License: MIT. See LICENSE

const flow_agent_card_view = {
	get storage_key() {
		return `flow_agent_card_view:${frappe.session.user || "Guest"}`;
	},

	is_enabled() {
		try {
			const saved = window.localStorage.getItem(this.storage_key);
			return saved === null ? true : saved === "1";
		} catch (_error) {
			return true;
		}
	},

	set_enabled(enabled) {
		try {
			window.localStorage.setItem(this.storage_key, enabled ? "1" : "0");
		} catch (_error) {
			// Storage can be unavailable in hardened browser profiles. The current
			// page still switches views; it simply will not remember the choice.
		}
	},

	init(listview) {
		this.add_styles();
		this.listview = listview;
	},

	refresh(listview) {
		this.listview = listview;
		this.ensure_view_toggle();
		this.render();
	},

	add_styles() {
		if (document.getElementById("flow-agent-card-view-styles")) {
			return;
		}

		const style = document.createElement("style");
		style.id = "flow-agent-card-view-styles";
		style.textContent = `
			.flow-agent-card-grid {
				display: grid;
				grid-template-columns: repeat(3, minmax(0, 1fr));
				gap: 18px;
				width: 100%;
				max-width: 1320px;
				margin: 6px auto 28px;
				padding: 2px;
			}

			.flow-agent-card {
				--flow-agent-accent: #5b6ee1;
				--flow-agent-accent-soft: #eef0ff;
				position: relative;
				display: flex;
				flex-direction: column;
				min-width: 0;
				min-height: 248px;
				padding: 20px;
				border: 1px solid var(--border-color);
				border-radius: 14px;
				background: var(--card-bg);
				box-shadow: 0 1px 2px rgba(17, 24, 39, 0.04);
				color: var(--text-color);
				text-align: left;
				transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
			}

			button.flow-agent-card {
				width: 100%;
				font: inherit;
				cursor: pointer;
			}

			button.flow-agent-card:hover,
			button.flow-agent-card:focus-visible {
				border-color: var(--flow-agent-accent);
				box-shadow: 0 10px 26px rgba(17, 24, 39, 0.09);
				transform: translateY(-2px);
				outline: none;
			}

			.flow-agent-card--accent-1 {
				--flow-agent-accent: #7c5ce7;
				--flow-agent-accent-soft: #f2edff;
			}

			.flow-agent-card--accent-2 {
				--flow-agent-accent: #2684ff;
				--flow-agent-accent-soft: #eaf3ff;
			}

			.flow-agent-card--accent-3 {
				--flow-agent-accent: #0b8f75;
				--flow-agent-accent-soft: #e7f7f2;
			}

			.flow-agent-card--accent-4 {
				--flow-agent-accent: #c47b16;
				--flow-agent-accent-soft: #fff4df;
			}

			.flow-agent-card--accent-5 {
				--flow-agent-accent: #d05c67;
				--flow-agent-accent-soft: #ffedef;
			}

			.flow-agent-card__header,
			.flow-agent-card__footer,
			.flow-agent-card__title-row,
			.flow-agent-card__status {
				display: flex;
				align-items: center;
			}

			.flow-agent-card__header {
				gap: 12px;
			}

			.flow-agent-card__icon {
				display: inline-flex;
				align-items: center;
				justify-content: center;
				width: 42px;
				height: 42px;
				flex: 0 0 42px;
				border-radius: 12px;
				background: var(--flow-agent-accent-soft);
				color: var(--flow-agent-accent);
			}

			.flow-agent-card__icon .icon {
				width: 20px;
				height: 20px;
			}

			.flow-agent-card__heading {
				min-width: 0;
				flex: 1;
			}

			.flow-agent-card__title-row {
				gap: 8px;
				min-width: 0;
			}

			.flow-agent-card__title {
				overflow: hidden;
				font-size: 16px;
				font-weight: 650;
				line-height: 1.35;
				text-overflow: ellipsis;
				white-space: nowrap;
			}

			.flow-agent-card__system {
				flex: 0 0 auto;
				padding: 2px 7px;
				border-radius: 999px;
				background: var(--subtle-fg);
				color: var(--text-muted);
				font-size: 11px;
				font-weight: 600;
			}

			.flow-agent-card__status {
				gap: 6px;
				margin-top: 3px;
				color: var(--text-muted);
				font-size: 12px;
			}

			.flow-agent-card__status-dot {
				width: 7px;
				height: 7px;
				border-radius: 999px;
				background: var(--gray-500);
			}

			.flow-agent-card__status--enabled .flow-agent-card__status-dot {
				background: var(--green-500);
				box-shadow: 0 0 0 3px var(--green-100);
			}

			.flow-agent-card__description {
				display: -webkit-box;
				overflow: hidden;
				min-height: 58px;
				margin: 17px 0 16px;
				color: var(--text-muted);
				font-size: 13px;
				line-height: 1.5;
				-webkit-box-orient: vertical;
				-webkit-line-clamp: 3;
			}

			.flow-agent-card__meta {
				display: grid;
				grid-template-columns: minmax(0, 1fr) minmax(0, 0.7fr);
				gap: 10px;
				padding: 12px;
				border-radius: 10px;
				background: var(--subtle-fg);
			}

			.flow-agent-card__meta-item {
				min-width: 0;
			}

			.flow-agent-card__meta-label {
				display: block;
				margin-bottom: 2px;
				color: var(--text-light);
				font-size: 11px;
			}

			.flow-agent-card__meta-value {
				display: block;
				overflow: hidden;
				font-size: 12px;
				font-weight: 600;
				text-overflow: ellipsis;
				white-space: nowrap;
			}

			.flow-agent-card__footer {
				justify-content: space-between;
				gap: 12px;
				margin-top: auto;
				padding-top: 15px;
				color: var(--text-light);
				font-size: 12px;
			}

			.flow-agent-card__open {
				display: inline-flex;
				align-items: center;
				gap: 4px;
				flex: 0 0 auto;
				color: var(--flow-agent-accent);
				font-weight: 600;
			}

			.flow-agent-card__open .icon {
				width: 13px;
				height: 13px;
			}

			.flow-agent-card--new {
				align-items: center;
				justify-content: center;
				border-style: dashed;
				background: color-mix(in srgb, var(--subtle-fg) 55%, transparent);
				color: var(--text-muted);
				text-align: center;
			}

			.flow-agent-card--new .flow-agent-card__icon {
				margin-bottom: 14px;
			}

			.flow-agent-card--new strong {
				display: block;
				margin-bottom: 5px;
				color: var(--text-color);
				font-size: 15px;
			}

			.flow-agent-card--new span:last-child {
				font-size: 12px;
			}

			@media (max-width: 1100px) {
				.flow-agent-card-grid {
					grid-template-columns: repeat(2, minmax(0, 1fr));
				}
			}

			@media (max-width: 767px) {
				.flow-agent-card-grid {
					grid-template-columns: minmax(0, 1fr);
					gap: 12px;
				}

				.flow-agent-card {
					min-height: 224px;
					padding: 16px;
				}
			}
		`;
		document.head.appendChild(style);
	},

	escape(value) {
		return frappe.utils.escape_html(String(value ?? ""));
	},

	plain_text(value) {
		const holder = document.createElement("div");
		holder.innerHTML = value || "";
		return (holder.textContent || "")
			.replace(/(^|\s)#{1,6}\s*/g, "$1")
			.replace(/\*\*|`/g, "")
			.replace(/\s+/g, " ")
			.trim();
	},

	get_accent(name) {
		let hash = 0;
		for (const character of String(name || "")) {
			hash = (hash * 31 + character.codePointAt(0)) % 5;
		}
		return hash + 1;
	},

	get_modified_label(value) {
		if (!value) {
			return "";
		}
		if (typeof comment_when === "function") {
			return comment_when(value, true);
		}
		return this.escape(value);
	},

	get_icon_name(value) {
		const icon = String(value || "bot").replace(/^icon-/, "");
		if (!/^[a-z0-9-]+$/.test(icon) || !document.getElementById(`icon-${icon}`)) {
			return "bot";
		}
		return icon;
	},

	get_card_html(doc) {
		const title = this.escape(doc.title || doc.name);
		const instructions = this.plain_text(doc.instructions) || "尚未配置智能体职责说明。";
		const summary =
			instructions.length > 180 ? `${instructions.slice(0, 177).trimEnd()}…` : instructions;
		const description = this.escape(summary);
		const model = this.escape(doc.model || "未配置");
		const iterations = this.escape(doc.max_iterations ?? "—");
		const status_class = doc.enabled ? "flow-agent-card__status--enabled" : "";
		const status_label = doc.enabled ? "已启用" : "未启用";
		const system_badge = doc.is_system_generated
			? '<span class="flow-agent-card__system">系统</span>'
			: "";
		const accent = this.get_accent(doc.name);
		const icon = this.get_icon_name(doc.card_icon);

		return `
			<button
				type="button"
				class="flow-agent-card flow-agent-card--accent-${accent}"
				data-flow-agent-name="${this.escape(doc.name)}"
				aria-label="打开 ${title}"
			>
				<div class="flow-agent-card__header">
					<span class="flow-agent-card__icon">${frappe.utils.icon(icon, "sm")}</span>
					<div class="flow-agent-card__heading">
						<div class="flow-agent-card__title-row">
							<span class="flow-agent-card__title" title="${title}">${title}</span>
							${system_badge}
						</div>
						<span class="flow-agent-card__status ${status_class}">
							<span class="flow-agent-card__status-dot"></span>
							${status_label}
						</span>
					</div>
				</div>
				<p class="flow-agent-card__description">${description}</p>
				<div class="flow-agent-card__meta">
					<div class="flow-agent-card__meta-item">
						<span class="flow-agent-card__meta-label">AI 模型</span>
						<span class="flow-agent-card__meta-value" title="${model}">${model}</span>
					</div>
					<div class="flow-agent-card__meta-item">
						<span class="flow-agent-card__meta-label">最大迭代</span>
						<span class="flow-agent-card__meta-value">${iterations} 次</span>
					</div>
				</div>
				<div class="flow-agent-card__footer">
					<span>更新于 ${this.get_modified_label(doc.modified)}</span>
					<span class="flow-agent-card__open">
						打开配置 ${frappe.utils.icon("chevron-right", "sm")}
					</span>
				</div>
			</button>
		`;
	},

	get_new_card_html() {
		return `
			<button type="button" class="flow-agent-card flow-agent-card--new flow-agent-card--accent-1">
				<span class="flow-agent-card__icon">${frappe.utils.icon("add", "sm")}</span>
				<strong>创建新智能体</strong>
				<span>配置职责、模型、工具和知识库</span>
			</button>
		`;
	},

	render() {
		const listview = this.listview;
		const result = listview?.$result?.[0];
		const container = result?.parentElement;
		if (!result || !container) {
			return;
		}

		container.querySelector(".flow-agent-card-grid")?.remove();

		if (!this.is_enabled()) {
			result.style.removeProperty("display");
			container.style.removeProperty("height");
			listview.set_result_height?.();
			this.update_view_button();
			return;
		}

		const grid = document.createElement("div");
		grid.className = "flow-agent-card-grid";
		grid.innerHTML = (listview.data || []).map((doc) => this.get_card_html(doc)).join("");
		if (listview.can_create && !frappe.boot.read_only) {
			grid.insertAdjacentHTML("beforeend", this.get_new_card_html());
		}

		grid.addEventListener("click", (event) => {
			const new_card = event.target.closest(".flow-agent-card--new");
			if (new_card) {
				listview.make_new_doc();
				return;
			}

			const card = event.target.closest("[data-flow-agent-name]");
			if (card) {
				frappe.set_route("Form", "Flow Agent", card.dataset.flowAgentName);
			}
		});

		result.style.display = "none";
		container.style.height = "auto";
		container.appendChild(grid);
		this.update_view_button();
	},

	get_view_group() {
		const menu = this.listview?.views_menu?.[0];
		return menu?.matches(".custom-btn-group") ? menu : menu?.closest(".custom-btn-group");
	},

	ensure_view_toggle() {
		const group = this.get_view_group();
		const menu = group?.querySelector(".dropdown-menu");
		if (!menu) {
			return;
		}

		let item = menu.querySelector("[data-flow-agent-card-toggle]");
		if (!item) {
			item = document.createElement("li");
			item.dataset.flowAgentCardToggle = "1";
			item.innerHTML = `
				<a class="grey-link dropdown-item" href="#" onclick="return false;">
					<span class="menu-item-icon flex align-items-center justify-items-center"></span>
					<span class="menu-item-label"></span>
				</a>
			`;
			item.addEventListener("click", (event) => {
				event.preventDefault();
				event.stopPropagation();
				this.set_enabled(!this.is_enabled());
				this.render();
				this.update_toggle_item();
				group.querySelector("button")?.click();
			});
			menu.prepend(item);
		}

		this.update_toggle_item();
	},

	update_toggle_item() {
		const group = this.get_view_group();
		const item = group?.querySelector("[data-flow-agent-card-toggle]");
		if (!item) {
			return;
		}

		const enabled = this.is_enabled();
		item.querySelector(".menu-item-icon").innerHTML = frappe.utils.icon(
			enabled ? "list" : "grid",
			"sm"
		);
		item.querySelector(".menu-item-label").textContent = enabled ? "列表视图" : "卡片视图";
	},

	update_view_button() {
		const group = this.get_view_group();
		const button = group?.querySelector("button");
		if (!button) {
			return;
		}

		const enabled = this.is_enabled();
		const label = button.querySelector(".custom-btn-group-label");
		if (label) {
			label.textContent = enabled ? "卡片视图" : "列表视图";
		}

		for (const use of button.querySelectorAll("use")) {
			if (use.getAttribute("href") !== "#icon-select") {
				use.setAttribute("href", enabled ? "#icon-grid" : "#icon-list");
			}
		}
	},
};

frappe.listview_settings["Flow Agent"] = {
	add_fields: ["instructions", "max_iterations", "is_system_generated", "card_icon"],

	onload(listview) {
		flow_agent_card_view.init(listview);
	},

	refresh(listview) {
		flow_agent_card_view.refresh(listview);
	},

	get_indicator(doc) {
		return doc.enabled
			? ["已启用", "blue", "enabled,=,1"]
			: ["未启用", "gray", "enabled,=,0"];
	},
};
