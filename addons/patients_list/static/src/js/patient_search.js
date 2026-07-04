/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

console.log("JS LOADED OK");

// ─── Fuzzy helpers ───────────────────────────────────────────────

function normalize(str) {
    return (str || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim();
}

function isSubsequence(abbr, word) {
    let i = 0;
    for (let j = 0; j < word.length && i < abbr.length; j++) {
        if (abbr[i] === word[j]) i++;
    }
    return i === abbr.length;
}

function levenshtein(a, b) {
    const m = a.length, n = b.length;
    const dp = Array.from({ length: m + 1 }, (_, i) => [i]);
    for (let j = 0; j <= n; j++) dp[0][j] = j;
    for (let i = 1; i <= m; i++) {
        for (let j = 1; j <= n; j++) {
            dp[i][j] = a[i-1] === b[j-1]
                ? dp[i-1][j-1]
                : 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
        }
    }
    return dp[m][n];
}

function wordScore(searchWord, nameWord) {
    if (nameWord === searchWord) return 0;
    if (nameWord.startsWith(searchWord)) return 0.5;
    if (nameWord.includes(searchWord)) return 1;
    if (isSubsequence(searchWord, nameWord)) return 2;
    const dist = levenshtein(searchWord, nameWord);
    const ratio = dist / Math.max(searchWord.length, nameWord.length);
    if (ratio <= 0.5) return 2 + ratio;
    return 99;
}

function patientScore(patient, searchWords) {
    const nameParts = normalize(patient.name).split(" ").filter(Boolean);
    let totalScore = 0;
    for (const sw of searchWords) {
        if (sw.length < 3) continue;
        let best = 99;
        for (const np of nameParts) {
            const s = wordScore(sw, np);
            if (s < best) best = s;
        }
        if (best === 99) return null;
        totalScore += best;
    }
    return totalScore;
}

function buildDomains(words) {
    if (words.length === 0) return [["id", "=", 0]];

    const conditions = [];
    for (const w of words) {
        const letter = w.slice(0, 1);
        conditions.push(["first_name", "ilike", letter]);
        conditions.push(["last_name",  "ilike", letter]);
        conditions.push(["name",       "ilike", letter]);
    }

    const domain = [];
    for (let i = 0; i < conditions.length - 1; i++) {
        domain.push("|");
    }
    return [...domain, ...conditions];
}

// ─── Composant ───────────────────────────────────────────────────

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
        this.debounceTimer = null;
        this.searchToken = 0;
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
        clearTimeout(this.debounceTimer);
        if (!this.state.query.trim()) {
            this.state.results = [];
            this.state.searched = false;
            return;
        }
        this.debounceTimer = setTimeout(() => this.onSearch(), 300);
    }

    async onSearch() {
        const raw = this.state.query.trim().replace(/\s+/g, " ");
        if (!raw) return;

        const token = ++this.searchToken;
        this.state.loading = true;
        this.state.searched = false;

        try {
            const searchWords = normalize(raw)
                .split(" ")
                .filter(w => w.length >= 3);

            if (searchWords.length === 0) {
                this.state.results = [];
                this.state.searched = true;
                return;
            }

            // 1. Pool large depuis Odoo (1ère lettre de chaque mot en OR)
            const domain = buildDomains(searchWords);
            const pool = await this.orm.searchRead(
                "patients",
                domain,
                ["name", "first_name", "last_name", "gender", "mobile", "email", "stage", "age"],
                { limit: 500 }
            );
            if (token !== this.searchToken) return; // une recherche plus récente a été lancée entre-temps

            // 2. Score + filtre côté JS
            const scored = [];
            for (const p of pool) {
                const score = patientScore(p, searchWords);
                if (score !== null) {
                    scored.push({ patient: p, score });
                }
            }

            // 3. Tri par score (meilleur = plus petit score en premier)
            scored.sort((a, b) => a.score - b.score);
            const results = scored.map(s => s.patient).slice(0, 50);

            // 4. Prochains RDV
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

                const appointmentMap = {};
                for (const apt of appointments) {
                    const patId = apt.patient[0];
                    if (!appointmentMap[patId]) appointmentMap[patId] = apt;
                }
                for (const patient of results) {
                    patient.next_appointment = appointmentMap[patient.id] || null;
                }
            }

            if (token !== this.searchToken) return; // idem : ignore si une recherche plus récente a démarré

            this.state.results = results;
            this.state.searched = true;

        } catch (error) {
            if (token !== this.searchToken) return;
            console.error("Erreur lors de la recherche:", error);
            this.state.results = [];
            this.state.searched = true;
        } finally {
            if (token === this.searchToken) this.state.loading = false;
        }
    }

    onKeyDown(ev) {
        if (ev.key === "Enter") {
            clearTimeout(this.debounceTimer);
            this.onSearch();
        }
    }

    onClear() {
        this.state.query = "";
        this.state.results = [];
        this.state.searched = false;
        if (this.searchInputRef.el) this.searchInputRef.el.focus();
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
            new:            "badge-new",
            contacted:      "badge-contacted",
            qualified:      "badge-qualified",
            consult_booked: "badge-consult",
            consult_done:   "badge-consult",
            plan_sent:      "badge-plan",
            pending:        "badge-pending",
            approved:       "badge-approved",
            deposit:        "badge-approved",
            scheduled:      "badge-scheduled",
            in_treatment:   "badge-treatment",
            completed:      "badge-completed",
            followup:       "badge-followup",
            closed:         "badge-closed",
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
            .map(w => w[0].toUpperCase())
            .join("");
    }
}

registry.category("actions").add("patients_list.patient_search_action", PatientSearchPage);