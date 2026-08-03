/** @odoo-module **/

import { Component, useState, onWillStart, useEffect, useRef, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";

const DASHBOARDS = [
    { id: "doctors", label: _t("Revenue by Doctor"), filters: ["date", "doctor", "reason", "patient"] },
    { id: "lab", label: _t("Dental Laboratory"), filters: ["date", "lab"] },
    { id: "crm", label: _t("Patients Pipeline (CRM)"), filters: ["date", "patient_type"] },
    { id: "appointments", label: _t("Appointments"), filters: ["date", "reason", "doctor", "patient"] },
    { id: "finance", label: _t("Finance / Treasury"), filters: ["date", "doctor", "patient"] },
    { id: "purchases", label: _t("Purchases & Suppliers"), filters: ["date", "supplier", "product"] },
    { id: "stock", label: _t("Stock & Inventory"), filters: ["category", "availability"] },
    { id: "expenses", label: _t("Expenses"), filters: ["date", "expense_type", "expense_status"] },
];

const FILTER_DEFS = {
    doctor: { optionsKey: "doctors", label: _t("Doctor"), param: "doctor_id" },
    reason: { optionsKey: "reasons", label: _t("Appointment Type"), param: "reason" },
    lab: { optionsKey: "labs", label: _t("Laboratory"), param: "lab_id" },
    patient_type: { optionsKey: "patient_types", label: _t("Patient Type"), param: "patient_type" },
    supplier: { optionsKey: "suppliers", label: _t("Supplier"), param: "supplier_id" },
    product: { optionsKey: "products", label: _t("Product"), param: "product_id" },
    category: { optionsKey: "product_categories", label: _t("Category"), param: "category_id" },
    availability: { optionsKey: "availabilities", label: _t("Availability"), param: "availability" },
    expense_type: { optionsKey: "expense_types", label: _t("Expense Type"), param: "expense_type_id" },
    expense_status: { optionsKey: "expense_statuses", label: _t("Status"), param: "status" },
};

function defaultDates() {
    const to = new Date();
    const from = new Date(to.getFullYear(), to.getMonth() - 5, 1);
    const iso = (d) =>
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
    return { date_from: iso(from), date_to: iso(to) };
}

export class TaibaStatsDashboard extends Component {
    static template = "taiba_stats.StatsDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.dashboards = DASHBOARDS;
        this.canvasRefs = [useRef("chart0"), useRef("chart1"), useRef("chart2")];
        this.chartInstances = [null, null, null];
        const dates = defaultDates();
        this.state = useState({
            active: "doctors",
            loading: true,
            data: null,
            options: null,
            error: "",
            filters: {
                date_from: dates.date_from,
                date_to: dates.date_to,
                doctor: "",
                reason: "",
                patient_name: "",
                lab: "",
                patient_type: "",
                supplier: "",
                product: "",
                category: "",
                availability: "",
                expense_type: "",
                expense_status: "",
            },
        });

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            this.state.options = await this.orm.call("taiba.stats", "get_filter_options", []);
            await this.loadData();
        });

        useEffect(
            () => {
                this.renderCharts();
                return () => this.destroyCharts();
            },
            () => [this.state.data]
        );

        onWillUnmount(() => this.destroyCharts());
    }

    get activeDash() {
        return this.dashboards.find((d) => d.id === this.state.active);
    }

    get activeSelectFilters() {
        return this.activeDash.filters
            .filter((k) => k !== "date" && k !== "patient")
            .map((k) => ({ key: k, ...FILTER_DEFS[k] }));
    }

    hasFilter(key) {
        return this.activeDash.filters.includes(key);
    }

    buildPayload() {
        const f = this.state.filters;
        const payload = {};
        if (this.hasFilter("date")) {
            payload.date_from = f.date_from || false;
            payload.date_to = f.date_to || false;
        }
        for (const sf of this.activeSelectFilters) {
            if (f[sf.key]) {
                payload[sf.param] = f[sf.key];
            }
        }
        if (this.hasFilter("patient") && f.patient_name) {
            const needle = f.patient_name.trim().toLowerCase();
            const match = (this.state.options.patients || []).find(
                (p) => p.name.toLowerCase() === needle
            );
            if (match) {
                payload.patient_id = match.id;
            }
        }
        return payload;
    }

    async loadData() {
        this.state.loading = true;
        this.state.error = "";
        try {
            this.state.data = await this.orm.call("taiba.stats", "get_dashboard", [
                this.state.active,
                this.buildPayload(),
            ]);
        } catch (e) {
            this.state.data = null;
            this.state.error = (e.data && e.data.message) || e.message || String(e);
        }
        this.state.loading = false;
    }

    async selectDash(id) {
        if (this.state.active === id) {
            return;
        }
        this.state.active = id;
        await this.loadData();
    }

    async applyFilters() {
        await this.loadData();
    }

    async resetFilters() {
        const dates = defaultDates();
        Object.assign(this.state.filters, {
            date_from: dates.date_from,
            date_to: dates.date_to,
            doctor: "",
            reason: "",
            patient_name: "",
            lab: "",
            patient_type: "",
            supplier: "",
            product: "",
            category: "",
            availability: "",
            expense_type: "",
            expense_status: "",
        });
        await this.loadData();
    }

    // ------------------------------------------------------------------
    // Charts
    // ------------------------------------------------------------------
    destroyCharts() {
        for (let i = 0; i < this.chartInstances.length; i++) {
            if (this.chartInstances[i]) {
                this.chartInstances[i].destroy();
                this.chartInstances[i] = null;
            }
        }
    }

    renderCharts() {
        this.destroyCharts();
        const data = this.state.data;
        if (!data || !window.Chart) {
            return;
        }
        data.charts.forEach((cfg, i) => {
            const el = this.canvasRefs[i].el;
            if (!el) {
                return;
            }
            this.chartInstances[i] = this.makeChart(el, cfg);
        });
    }

    makeChart(canvas, cfg) {
        const fmt = this.fmt.bind(this);
        let datasets;
        if (cfg.multi) {
            datasets = cfg.data.map((d, i) => ({
                label: cfg.mlabels[i],
                data: d,
                borderColor: cfg.colors[i],
                backgroundColor: cfg.colors[i],
                borderWidth: 2,
                tension: 0.3,
                pointRadius: 2,
                fill: false,
            }));
        } else if (cfg.type === "doughnut") {
            datasets = [
                {
                    data: cfg.data,
                    backgroundColor: cfg.colors,
                    borderColor: "#ffffff",
                    borderWidth: 2,
                },
            ];
        } else if (cfg.type === "line") {
            datasets = [
                {
                    data: cfg.data,
                    borderColor: cfg.colors[0],
                    backgroundColor: cfg.colors[0],
                    borderWidth: 2,
                    tension: 0.3,
                    pointRadius: 2,
                    fill: false,
                },
            ];
        } else {
            datasets = [
                {
                    data: cfg.data,
                    backgroundColor: cfg.colors[0],
                    borderRadius: 4,
                    maxBarThickness: 24,
                },
            ];
        }
        return new window.Chart(canvas, {
            type: cfg.type === "doughnut" ? "doughnut" : cfg.type === "line" ? "line" : "bar",
            data: { labels: cfg.labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label(c) {
                                if (cfg.type === "doughnut") {
                                    return c.label + ": " + c.parsed + "%";
                                }
                                const v = c.parsed.y !== undefined ? c.parsed.y : c.parsed;
                                return (c.dataset.label ? c.dataset.label + ": " : "") + fmt(v);
                            },
                        },
                    },
                },
                scales:
                    cfg.type === "doughnut"
                        ? {}
                        : {
                              y: {
                                  ticks: { color: "#898781", font: { size: 10 } },
                                  grid: { color: "#e1e0d9" },
                              },
                              x: {
                                  ticks: { color: "#898781", font: { size: 10 } },
                                  grid: { display: false },
                              },
                          },
            },
        });
    }

    legendFor(cfg) {
        if (!cfg) {
            return [];
        }
        if (cfg.multi) {
            return cfg.mlabels.map((l, i) => ({ label: l, color: cfg.colors[i] }));
        }
        if (cfg.type === "doughnut") {
            return cfg.labels.map((l, i) => ({
                label: `${l} ${cfg.data[i]}%`,
                color: cfg.colors[i % cfg.colors.length],
            }));
        }
        return [];
    }

    fmt(v) {
        return new Intl.NumberFormat(document.documentElement.lang || "fr-DZ").format(v || 0);
    }
}

registry.category("actions").add("taiba_stats_dashboard", TaibaStatsDashboard);
