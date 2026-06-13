/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const MONTHS = [
    "Janvier","Fevrier","Mars","Avril","Mai","Juin",
    "Juillet","Aout","Septembre","Octobre","Novembre","Decembre"
];

class DoctorDashboard extends Component {
    static template = "doctors_list.DoctorDashboard";

    setup() {
        this.orm = useService("orm");
        const now = new Date();
        this.state = useState({
            month:   now.getMonth() + 1,
            year:    now.getFullYear(),
            data:    null,
            loading: true,
        });
        onWillStart(() => this.loadData());
    }

    async loadData() {
        this.state.loading = true;
        this.state.data = await this.orm.call(
            "doctor.dashboard",
            "get_dashboard_data",
            [this.state.month, this.state.year]
        );
        this.state.loading = false;
    }

    async prevMonth() {
        if (this.state.month === 1) { this.state.month = 12; this.state.year--; }
        else { this.state.month--; }
        await this.loadData();
    }

    async nextMonth() {
        if (this.state.month === 12) { this.state.month = 1; this.state.year++; }
        else { this.state.month++; }
        await this.loadData();
    }

    async goCurrentMonth() {
        const now = new Date();
        this.state.month = now.getMonth() + 1;
        this.state.year  = now.getFullYear();
        await this.loadData();
    }

    get monthLabel() {
        return MONTHS[this.state.month - 1] + " " + this.state.year;
    }

    get isCurrentMonth() {
        const now = new Date();
        return this.state.month === now.getMonth() + 1 && this.state.year === now.getFullYear();
    }

    fmt(amount) {
        return new Intl.NumberFormat("fr-DZ", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        }).format(amount || 0) + " DA";
    }

    initials(name) {
        if (!name) return "?";
        return name.split(" ").filter(Boolean).map(w => w[0]).slice(0, 2).join("").toUpperCase();
    }

    clinicPct(docPct) { return 100 - (docPct || 0); }

    clinicRate() {
        if (!this.state.data || !this.state.data.stats.total_net) return 0;
        const s = this.state.data.stats;
        return Math.round(s.total_clinic_earnings / s.total_net * 100);
    }
}

registry.category("actions").add("doctor_dashboard", DoctorDashboard);