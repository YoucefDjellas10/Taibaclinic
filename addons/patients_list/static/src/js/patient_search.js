/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { DateTime } from "@web/core/l10n/dates";
console.log("JS LOADED OK");
class PatientSearchPage extends Component {
    static template = "patients_list.PatientSearchPage";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            query: "",
            results: [],
            searched: false,
            loading: false,
        });

        this.searchInputRef = useRef("searchInput");
    }

    get labels() {
        return {
            clinicName:    _t("Taiba Dental Clinic"),
            title:         _t("Patient Search"),
            subtitle:      _t("Search by first name, last name or full name"),
            placeholder:   _t("Enter patient first name, last name or full name..."),
            search:        _t("Search"),
            searching:     _t("Searching..."),
            newBtn:        _t("New"),
            loadingText:   _t("Searching..."),
            noResultTitle: _t("No results found"),
            noResultMsg:   _t("No patient matches"),
            noResultHint:  _t("Check the spelling or try another term."),
            initialMsg:    _t("Use the search bar above to find a patient."),
            resultFor:     _t("result(s) for"),
            years:         _t("years"),
        };
    }

    onInputChange(ev) {
        this.state.query = ev.target.value;
        if (!this.state.query.trim()) {
            this.state.results = [];
            this.state.searched = false;
        }
    }

    async onSearch() {
        const query = this.state.query.trim().replace(/\s+/g, " ");
        if (!query) return;

        this.state.loading = true;
        this.state.searched = false;

        try {
            const words = query.split(" ").filter(Boolean);
            let results = [];

            if (words.length >= 2) {
                const word1 = words[0];
                const word2 = words[1];

                const r1 = await this.orm.searchRead(
                    "patients",
                    [["name", "ilike", query]],
                    ["name", "first_name", "last_name", "gender", "mobile", "email", "stage", "age"],
                    { limit: 50 }
                );
                const r2 = await this.orm.searchRead(
                    "patients",
                    [["name", "ilike", `${word2} ${word1}`]],
                    ["name", "first_name", "last_name", "gender", "mobile", "email", "stage", "age"],
                    { limit: 50 }
                );
                const r3 = await this.orm.searchRead(
                    "patients",
                    [["first_name", "ilike", word1], ["last_name", "ilike", word2]],
                    ["name", "first_name", "last_name", "gender", "mobile", "email", "stage", "age"],
                    { limit: 50 }
                );
                const r4 = await this.orm.searchRead(
                    "patients",
                    [["first_name", "ilike", word2], ["last_name", "ilike", word1]],
                    ["name", "first_name", "last_name", "gender", "mobile", "email", "stage", "age"],
                    { limit: 50 }
                );

                const seen = new Set();
                for (const r of [...r1, ...r2, ...r3, ...r4]) {
                    if (!seen.has(r.id)) {
                        seen.add(r.id);
                        results.push(r);
                    }
                }
            } else {
                results = await this.orm.searchRead(
                    "patients",
                    ["|", "|",
                        ["first_name", "ilike", query],
                        ["last_name", "ilike", query],
                        ["name", "ilike", query],
                    ],
                    ["name", "first_name", "last_name", "gender", "mobile", "email", "stage", "age"],
                    { limit: 50 }
                );
            }

            // Récupérer les prochains RDV
            if (results.length > 0) {
                const patientIds = results.map(p => p.id);
                const today = new Date().toISOString().slice(0, 19).replace("T", " ");

                const appointments = await this.orm.searchRead(
                    "appointment.record",
                    [
                        ["patient", "in", patientIds],
                        ["date", ">=", today],
                        ["status", "in", ["scheduled", "confirmed"]],
                    ],
                    ["patient", "date", "reason"],
                    { order: "date asc", limit: 200 }
                );

                // Garder le premier RDV par patient
                const appointmentMap = {};
                for (const apt of appointments) {
                    const patId = apt.patient[0];
                    if (!appointmentMap[patId]) {
                        appointmentMap[patId] = apt;
                    }
                }

                // Attacher le RDV à chaque patient
                for (const patient of results) {
                    patient.next_appointment = appointmentMap[patient.id] || null;
                }
            }

            this.state.results = results;
            this.state.searched = true;

        } catch (error) {
            console.error("Erreur lors de la recherche:", error);
            this.state.results = [];
            this.state.searched = true;
        } finally {
            this.state.loading = false;
        }
    }

    onKeyDown(ev) {
        if (ev.key === "Enter") {
            this.onSearch();
        }
    }

    onClear() {
        this.state.query = "";
        this.state.results = [];
        this.state.searched = false;
        if (this.searchInputRef.el) {
            this.searchInputRef.el.focus();
        }
    }

    openPatient(patientId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "patients",
            res_id: patientId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    openNewPatient() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "patients",
            views: [[false, "form"]],
            target: "current",
        });
    }

    getStageBadgeClass(stage) {
        const map = {
            new:           "badge-new",
            contacted:     "badge-contacted",
            qualified:     "badge-qualified",
            consult_booked:"badge-consult",
            consult_done:  "badge-consult",
            plan_sent:     "badge-plan",
            pending:       "badge-pending",
            approved:      "badge-approved",
            deposit:       "badge-approved",
            scheduled:     "badge-scheduled",
            in_treatment:  "badge-treatment",
            completed:     "badge-completed",
            followup:      "badge-followup",
            closed:        "badge-closed",
        };
        return map[stage] || "badge-default";
    }

    getStageLabel(stage) {
        const labels = {
            new:            _t("New Lead"),
            contacted:      _t("Contacted"),
            qualified:      _t("Qualified"),
            consult_booked: _t("Consult Booked"),
            consult_done:   _t("Consult Done"),
            plan_sent:      _t("Plan Sent"),
            pending:        _t("Pending"),
            approved:       _t("Approved"),
            deposit:        _t("Deposit Paid"),
            scheduled:      _t("Scheduled"),
            in_treatment:   _t("In Treatment"),
            completed:      _t("Completed"),
            followup:       _t("Follow-up"),
            closed:         _t("Closed"),
        };
        return labels[stage] || stage;
    }

    getReasonLabel(reason) {
        const reasons = {
            consultation:   _t("General Consultation"),
            checkup:        _t("Dental Check-up"),
            cleaning:       _t("Scaling / Cleaning"),
            whitening:      _t("Teeth Whitening"),
            cavity:         _t("Cavity Treatment"),
            extraction:     _t("Tooth Extraction"),
            implant:        _t("Dental Implant"),
            prosthesis:     _t("Dental Prosthesis"),
            crown:          _t("Dental Crown"),
            veneer:         _t("Veneers"),
            orthodontics:   _t("Orthodontics"),
            root_canal:     _t("Root Canal"),
            emergency:      _t("Emergency"),
            oral_surgery:   _t("Oral Surgery"),
            tooth_pain:     _t("Tooth Pain"),
            pediatric:      _t("Pediatric Dentistry"),
            xray:           _t("X-Ray / Scan"),
            treatment_plan: _t("Treatment Plan / Quote"),
            followup:       _t("Follow-up"),
            other:          _t("Other"),
        };
        return reasons[reason] || reason;
    }

    formatDate(dateStr) {
        if (!dateStr) return "";
        const date = new Date(dateStr + "Z");

        return date.toLocaleString("fr-FR", {
            day: "2-digit",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            timeZone: "Africa/Algiers",
        });
    }



    getInitials(name) {
        if (!name) return "?";
        return name
            .split(" ")
            .filter(Boolean)
            .slice(0, 2)
            .map((w) => w[0].toUpperCase())
            .join("");
    }
}

registry.category("actions").add("patients_list.patient_search_action", PatientSearchPage);