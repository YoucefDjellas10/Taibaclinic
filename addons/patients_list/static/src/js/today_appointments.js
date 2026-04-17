/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TodayAppointmentsPage extends Component {
    static template = "patients_list.TodayAppointmentsPage";

    setup() {
        this.orm    = useService("orm");
        this.action = useService("action");

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        this.state = useState({
            appointments: [],
            loading:      true,
            filter:       "all",
            currentDate:  today,
        });

        onWillStart(async () => {
            await this._loadAppointments();
        });
    }

    // ── Date helpers ──────────────────────────────────────────────────────────

    get _today() {
        const d = new Date();
        d.setHours(0, 0, 0, 0);
        return d;
    }

    get _dayOffset() {
        const diff = this.state.currentDate.getTime() - this._today.getTime();
        return Math.round(diff / 86400000);
    }

    get dateTitle() {
        const offset = this._dayOffset;
        if (offset ===  0) return "Today's Appointments";
        if (offset ===  1) return "Tomorrow's Appointments";
        if (offset === -1) return "Yesterday's Appointments";
        return `Appointments — ${this._formatFull(this.state.currentDate)}`;
    }

    get dateSubtitle() {
        const offset = this._dayOffset;
        const full   = this._formatFull(this.state.currentDate);
        if (offset ===  0) return `Today · ${full}`;
        if (offset ===  1) return `Tomorrow · ${full}`;
        if (offset === -1) return `Yesterday · ${full}`;
        return full;
    }

    get isToday() { return this._dayOffset === 0; }

    _formatFull(date) {
        return date.toLocaleDateString([], {
            weekday: "long", day: "numeric", month: "long", year: "numeric",
        });
    }

    _pad(n) { return String(n).padStart(2, "0"); }

    _toOdooDatetime(date, endOfDay = false) {
        const y = date.getFullYear();
        const m = this._pad(date.getMonth() + 1);
        const d = this._pad(date.getDate());
        return endOfDay
            ? `${y}-${m}-${d} 23:59:59`
            : `${y}-${m}-${d} 00:00:00`;
    }

    // ── Navigation ────────────────────────────────────────────────────────────

    async goToPrevDay() {
        const d = new Date(this.state.currentDate);
        d.setDate(d.getDate() - 1);
        this.state.currentDate = d;
        await this._loadAppointments();
    }

    async goToNextDay() {
        const d = new Date(this.state.currentDate);
        d.setDate(d.getDate() + 1);
        this.state.currentDate = d;
        await this._loadAppointments();
    }

    async goToToday() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        this.state.currentDate = today;
        await this._loadAppointments();
    }

    // ── Data loading ──────────────────────────────────────────────────────────

    async _loadAppointments() {
        this.state.loading = true;
        try {
            const start = this._toOdooDatetime(this.state.currentDate, false);
            const end   = this._toOdooDatetime(this.state.currentDate, true);

            const records = await this.orm.searchRead(
                "appointment.record",
                [["date", ">=", start], ["date", "<=", end]],
                ["id", "name", "patient", "date", "reason", "status", "doctor", "note"],
                { order: "date asc" }
            );

            const patientIds = [...new Set(records.map(r => r.patient[0]).filter(Boolean))];
            let patientMap = {};
            if (patientIds.length) {
                const patients = await this.orm.searchRead(
                    "patients",
                    [["id", "in", patientIds]],
                    ["id", "name", "age", "mobile", "email"]
                );
                patientMap = Object.fromEntries(patients.map(p => [p.id, p]));
            }

            this.state.appointments = records.map(r => ({
                ...r,
                patientInfo: patientMap[r.patient[0]] || {},
            }));
        } catch (e) {
            console.error("TodayAppointments: failed to load", e);
            this.state.appointments = [];
        } finally {
            this.state.loading = false;
        }
    }

    async refreshAppointments() {
        await this._loadAppointments();
    }

    // ── Filters ───────────────────────────────────────────────────────────────

    get filterOptions() {
        return [
            { key: "all",         label: "All"          },
            { key: "scheduled",   label: "Scheduled"    },
            { key: "confirmed",   label: "Confirmed"    },
            { key: "in_progress", label: "In Treatment" },
            { key: "completed",   label: "Completed"    },
            { key: "cancelled",   label: "Cancelled"    },
        ];
    }

    get filteredAppointments() {
        if (this.state.filter === "all") return this.state.appointments;
        return this.state.appointments.filter(a => a.status === this.state.filter);
    }

    setFilter(key) { this.state.filter = key; }

    // ── Counters ──────────────────────────────────────────────────────────────

    get countUpcoming() {
        return this.state.appointments.filter(
            a => a.status === "scheduled" || a.status === "confirmed"
        ).length;
    }
    get countActive() {
        return this.state.appointments.filter(a => a.status === "in_progress").length;
    }
    get countDone() {
        return this.state.appointments.filter(a => a.status === "completed").length;
    }

    // ── Label maps ────────────────────────────────────────────────────────────

    stageMap = {
        scheduled:   { label: "Scheduled",    cls: "badge-scheduled" },
        confirmed:   { label: "Confirmed",    cls: "badge-qualified" },
        in_progress: { label: "In Treatment", cls: "badge-treatment" },
        completed:   { label: "Completed",    cls: "badge-completed" },
        cancelled:   { label: "Cancelled",    cls: "badge-closed"    },
    };

    reasonMap = {
        consultation:   "General Consultation",
        checkup:        "Dental Check-up",
        cleaning:       "Scaling / Cleaning",
        whitening:      "Teeth Whitening",
        cavity:         "Cavity Treatment",
        extraction:     "Tooth Extraction",
        implant:        "Dental Implant",
        prosthesis:     "Dental Prosthesis",
        crown:          "Dental Crown",
        veneer:         "Veneers",
        orthodontics:   "Orthodontics",
        root_canal:     "Root Canal",
        emergency:      "Emergency",
        oral_surgery:   "Oral Surgery",
        tooth_pain:     "Tooth Pain",
        pediatric:      "Pediatric Dentistry",
        xray:           "X-Ray / Scan",
        treatment_plan: "Treatment Plan / Quote",
        followup:       "Follow-up",
        other:          "Other",
    };

    getInitials(name) {
        if (!name) return "?";
        return name.split(" ").slice(0, 2).map(w => w[0]?.toUpperCase() || "").join("");
    }

    getStatusLabel(status)      { return this.stageMap[status]?.label || status; }
    getStatusBadgeClass(status) { return this.stageMap[status]?.cls   || "badge-default"; }
    getReasonLabel(reason)      { return this.reasonMap[reason]        || reason; }

    formatTime(dateStr) {
        if (!dateStr) return "";
        return new Date(dateStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    isUpcoming(dateStr) { return new Date(dateStr) > new Date(); }

    // ── Actions ───────────────────────────────────────────────────────────────

    openAppointment(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "appointment.record",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openNewAppointment() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "appointment.record",
            views: [[false, "form"]],
            target: "current",
        });
    }

    openPatient(patientId) {
        if (!patientId) return;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "patients",
            res_id: patientId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry.category("actions").add("today_appointments_action", TodayAppointmentsPage);