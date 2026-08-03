from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.exceptions import AccessError
from odoo.tools.misc import format_date, format_datetime

BLUE = '#2a78d6'
CORAL = '#e34948'
PALETTE = ['#2a78d6', '#1baf7a', '#eda100', '#008300', '#4a3aa7',
           '#e34948', '#e87ba4', '#eb6834', '#0e7f97', '#8f6b2f']
GOOD = '#0ca30c'
WARN = '#fab219'
CRIT = '#d03b3b'


class TaibaStats(models.AbstractModel):
    _name = 'taiba.stats'
    _description = 'Taiba Clinic Statistics Dashboard'

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _check_access(self):
        user = self.env.user
        if not (user.has_group('access_rights.group_admin')
                or user.has_group('access_rights.group_ceo')
                or user.has_group('base.group_system')):
            raise AccessError(self.env._("You are not allowed to access the statistics dashboard."))

    def _period(self, filters):
        today = date.today()
        dto = self._to_date(filters.get('date_to')) or today
        dfrom = self._to_date(filters.get('date_from')) or (today.replace(day=1) - relativedelta(months=5))
        if dfrom > dto:
            dfrom, dto = dto, dfrom
        return dfrom, dto

    @staticmethod
    def _to_date(value):
        if not value:
            return False
        return date.fromisoformat(str(value)[:10])

    @staticmethod
    def _dom_dt(field, dfrom, dto):
        return [(field, '>=', f'{dfrom} 00:00:00'), (field, '<=', f'{dto} 23:59:59')]

    @staticmethod
    def _dom_d(field, dfrom, dto):
        return [(field, '>=', str(dfrom)), (field, '<=', str(dto))]

    @staticmethod
    def _int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _months(dfrom, dto):
        months = []
        d = dfrom.replace(day=1)
        end = dto.replace(day=1)
        while d <= end and len(months) < 36:
            months.append(d)
            d += relativedelta(months=1)
        return months

    def _mlabel(self, d):
        return format_date(self.env, d, date_format='MMM yy')

    def _money(self, value):
        return f"{round(value or 0.0):,}".replace(',', ' ') + " DA"

    def _sel(self, model, fname):
        field = self.env[model]._fields[fname]
        return [(value, self.env._(label)) for value, label in field._description_selection(self.env)]

    def _sel_map(self, model, fname):
        return dict(self._sel(model, fname))

    @staticmethod
    def _pcts(values):
        total = sum(values) or 1.0
        return [round(100.0 * v / total) for v in values]

    # ------------------------------------------------------------------
    # Filter options (dropdown contents)
    # ------------------------------------------------------------------
    @api.model
    def get_filter_options(self):
        self._check_access()
        env = self.env

        def m2o(model):
            return [{'id': r.id, 'name': r.display_name} for r in env[model].search([])]

        def sel(model, fname):
            return [{'id': value, 'name': label} for value, label in self._sel(model, fname)]

        return {
            'doctors': m2o('doctors'),
            'patients': m2o('patients'),
            'labs': m2o('laboratory.list'),
            'suppliers': m2o('supplier.record'),
            'products': m2o('product.record'),
            'expense_types': m2o('expense.type.record'),
            'product_categories': m2o('product.category.record'),
            'reasons': sel('appointment.record', 'reason'),
            'patient_types': sel('patients', 'patient_type'),
            'availabilities': sel('product.record', 'availability'),
            'expense_statuses': sel('expense.record', 'status'),
        }

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard(self, dash, filters=None):
        self._check_access()
        filters = filters or {}
        dfrom, dto = self._period(filters)
        handlers = {
            'doctors': self._dash_doctors,
            'lab': self._dash_lab,
            'crm': self._dash_crm,
            'appointments': self._dash_appointments,
            'finance': self._dash_finance,
            'purchases': self._dash_purchases,
            'stock': self._dash_stock,
            'expenses': self._dash_expenses,
        }
        if dash not in handlers:
            raise ValueError(f"Unknown dashboard: {dash}")
        result = handlers[dash](filters, dfrom, dto)
        result['period'] = {'date_from': str(dfrom), 'date_to': str(dto)}
        return result

    # ------------------------------------------------------------------
    # 1. Revenue by doctor
    # ------------------------------------------------------------------
    def _dash_doctors(self, f, dfrom, dto):
        _ = self.env._
        dom = self._dom_dt('date', dfrom, dto) + [('status', '!=', 'cancelled')]
        if self._int(f.get('doctor_id')):
            dom.append(('doctor', '=', self._int(f['doctor_id'])))
        if f.get('reason'):
            dom.append(('reason', '=', f['reason']))
        if self._int(f.get('patient_id')):
            dom.append(('patient', '=', self._int(f['patient_id'])))
        apps = self.env['appointment.record'].search(dom)

        per = {}
        monthly = {}
        for a in apps:
            key = a.doctor.id or 0
            rec = per.setdefault(key, {
                'name': a.doctor.name or _("No doctor"),
                'pct': a.doctor.percentage or 0,
                'count': 0, 'gross': 0.0, 'labo': 0.0,
            })
            rec['count'] += 1
            rec['gross'] += a.net_total
            rec['labo'] += a.total_payments_labo
            if a.date:
                mk = (a.date.year, a.date.month)
                m = monthly.setdefault(mk, {'gross': 0.0, 'labo': 0.0})
                m['gross'] += a.net_total
                m['labo'] += a.total_payments_labo

        rows = []
        tot_gross = tot_labo = tot_doc = tot_clinic = 0.0
        for rec in per.values():
            net = rec['gross'] - rec['labo']
            doc_earn = net * rec['pct'] / 100.0
            clinic = net - doc_earn
            tot_gross += rec['gross']
            tot_labo += rec['labo']
            tot_doc += doc_earn
            tot_clinic += clinic
            rows.append({**rec, 'net': net, 'doc_earn': doc_earn, 'clinic': clinic})
        rows.sort(key=lambda r: -r['net'])

        months = self._months(dfrom, dto)
        month_net = [monthly.get((m.year, m.month), {'gross': 0.0, 'labo': 0.0}) for m in months]

        return {
            'kpis': [
                [_("Gross Revenue"), self._money(tot_gross)],
                [_("Clinic Share"), self._money(tot_clinic)],
                [_("Doctors Share"), self._money(tot_doc)],
                [_("Appointments"), str(len(apps))],
            ],
            'charts': [
                {'type': 'bar', 'title': _("Net revenue by doctor (DA)"),
                 'labels': [r['name'] for r in rows[:10]],
                 'data': [round(r['net']) for r in rows[:10]], 'colors': [BLUE]},
                {'type': 'doughnut', 'title': _("Revenue split"),
                 'labels': [_("Clinic Share"), _("Doctors Share")],
                 'data': self._pcts([tot_clinic, tot_doc]), 'colors': [BLUE, PALETTE[2]]},
                {'type': 'line', 'title': _("Monthly net revenue (DA)"),
                 'labels': [self._mlabel(m) for m in months],
                 'data': [round(m['gross'] - m['labo']) for m in month_net], 'colors': [BLUE]},
            ],
            'table': {
                'cols': [_("Doctor"), _("Appointments"), _("Gross Revenue"), _("Lab Cost"),
                         _("Net Revenue"), "%", _("Doctor Earnings"), _("Clinic Earnings")],
                'rows': [[r['name'], str(r['count']), self._money(r['gross']), self._money(r['labo']),
                          self._money(r['net']), f"{r['pct']}%", self._money(r['doc_earn']),
                          self._money(r['clinic'])] for r in rows],
            },
        }

    # ------------------------------------------------------------------
    # 2. Dental laboratory
    # ------------------------------------------------------------------
    def _dash_lab(self, f, dfrom, dto):
        _ = self.env._
        dom = self._dom_d('order_date', dfrom, dto)
        if self._int(f.get('lab_id')):
            dom.append(('lab_id', '=', self._int(f['lab_id'])))
        orders = self.env['dental.lab.order'].search(dom)

        open_states = ('confirmed', 'sent', 'manufacturing', 'fitting', 'rework', 'validated')
        open_orders = orders.filtered(lambda o: o.state in open_states)
        urgent = orders.filtered(lambda o: o.priority != '0'
                                 and o.state not in ('delivered', 'placed', 'invoiced', 'cancelled'))
        delays = [(o.received_date - o.sent_date).days
                  for o in orders if o.received_date and o.sent_date]
        avg_delay = round(sum(delays) / len(delays), 1) if delays else 0.0
        unpaid = sum(o.amount_remaining for o in orders if o.state != 'cancelled')

        state_labels = self._sel_map('dental.lab.order', 'state')
        state_counts = {}
        for o in orders:
            state_counts[o.state] = state_counts.get(o.state, 0) + 1
        state_keys = [k for k, __ in self._sel('dental.lab.order', 'state') if state_counts.get(k)]

        lab_amounts = {}
        for o in orders.filtered(lambda o: o.state != 'cancelled'):
            lab_amounts.setdefault(o.lab_id.name, 0.0)
            lab_amounts[o.lab_id.name] += o.amount_total
        lab_items = sorted(lab_amounts.items(), key=lambda i: -i[1])

        wt_labels = self._sel_map('dental.lab.order', 'work_type')
        wt_counts = {}
        for o in orders:
            wt_counts[o.work_type] = wt_counts.get(o.work_type, 0) + 1
        wt_keys = [k for k, __ in self._sel('dental.lab.order', 'work_type') if wt_counts.get(k)]

        recent = orders.sorted(key=lambda o: (o.order_date or date.min, o.id), reverse=True)[:10]

        return {
            'kpis': [
                [_("Open Orders"), str(len(open_orders))],
                [_("Urgent"), str(len(urgent))],
                [_("Avg Turnaround (days)"), str(avg_delay)],
                [_("Lab Unpaid"), self._money(unpaid)],
            ],
            'charts': [
                {'type': 'bar', 'title': _("Orders by status"),
                 'labels': [state_labels[k] for k in state_keys],
                 'data': [state_counts[k] for k in state_keys], 'colors': [BLUE]},
                {'type': 'doughnut', 'title': _("Share by laboratory"),
                 'labels': [i[0] for i in lab_items[:6]],
                 'data': self._pcts([i[1] for i in lab_items[:6]]),
                 'colors': PALETTE},
                {'type': 'bar', 'title': _("Orders by work type"),
                 'labels': [wt_labels[k] for k in wt_keys],
                 'data': [wt_counts[k] for k in wt_keys], 'colors': [BLUE]},
            ],
            'table': {
                'cols': [_("Reference"), _("Laboratory"), _("Doctor"), _("Work Type"),
                         _("Status"), _("Total"), _("Expected Date")],
                'rows': [[o.name or '', o.lab_id.name or '', o.doctor_id.name or '',
                          wt_labels.get(o.work_type, ''), state_labels.get(o.state, ''),
                          self._money(o.amount_total),
                          format_date(self.env, o.expected_date) if o.expected_date else '-']
                         for o in recent],
            },
        }

    # ------------------------------------------------------------------
    # 3. CRM pipeline (door + leads)
    # ------------------------------------------------------------------
    def _dash_crm(self, f, dfrom, dto):
        _ = self.env._
        dom = self._dom_dt('create_date', dfrom, dto)
        if f.get('patient_type'):
            dom.append(('patient_type', '=', f['patient_type']))
        pats = self.env['patients'].search(dom)

        doors = pats.filtered(lambda p: p.patient_type == 'door')
        leads = pats.filtered(lambda p: p.patient_type == 'lead')
        closed = leads.filtered(lambda p: p.stage == 'deal_closed')
        conv = round(100.0 * len(closed) / len(leads)) if leads else 0

        stage_labels = self._sel_map('patients', 'stage')
        stage_counts = {}
        for p in pats:
            stage_counts[p.stage] = stage_counts.get(p.stage, 0) + 1
        stage_keys = [k for k, __ in self._sel('patients', 'stage') if stage_counts.get(k)]

        type_labels = self._sel_map('patients', 'patient_type')
        type_counts = {}
        for p in pats:
            type_counts[p.patient_type] = type_counts.get(p.patient_type, 0) + 1
        type_keys = [k for k, __ in self._sel('patients', 'patient_type') if type_counts.get(k)]

        months = self._months(dfrom, dto)
        door_m = {(m.year, m.month): 0 for m in months}
        lead_m = {(m.year, m.month): 0 for m in months}
        for p in pats:
            if not p.create_date:
                continue
            mk = (p.create_date.year, p.create_date.month)
            if p.patient_type == 'door' and mk in door_m:
                door_m[mk] += 1
            elif p.patient_type == 'lead' and mk in lead_m:
                lead_m[mk] += 1

        recent = pats.sorted(key=lambda p: p.create_date or False, reverse=True)[:10]

        return {
            'kpis': [
                [_("New Patients"), str(len(pats))],
                [_("Door Patients"), str(len(doors))],
                [_("Leads"), str(len(leads))],
                [_("Conversion Rate"), f"{conv}%"],
            ],
            'charts': [
                {'type': 'bar', 'title': _("Patients by stage"),
                 'labels': [stage_labels[k] for k in stage_keys],
                 'data': [stage_counts[k] for k in stage_keys], 'colors': [BLUE]},
                {'type': 'doughnut', 'title': _("Patients by type"),
                 'labels': [type_labels[k] for k in type_keys],
                 'data': self._pcts([type_counts[k] for k in type_keys]),
                 'colors': PALETTE},
                {'type': 'line', 'title': _("New patients per month"),
                 'multi': True, 'mlabels': [_("Door"), _("Leads")],
                 'labels': [self._mlabel(m) for m in months],
                 'data': [[door_m[(m.year, m.month)] for m in months],
                          [lead_m[(m.year, m.month)] for m in months]],
                 'colors': [BLUE, CORAL]},
            ],
            'table': {
                'cols': [_("Patient"), _("Patient Type"), _("Stage"), _("Salesperson"), _("Date")],
                'rows': [[p.name or '', type_labels.get(p.patient_type, ''),
                          stage_labels.get(p.stage, ''), p.salesperson.name or '-',
                          format_datetime(self.env, p.create_date) if p.create_date else '-']
                         for p in recent],
            },
        }

    # ------------------------------------------------------------------
    # 4. Appointments
    # ------------------------------------------------------------------
    def _dash_appointments(self, f, dfrom, dto):
        _ = self.env._
        dom = self._dom_dt('date', dfrom, dto)
        if f.get('reason'):
            dom.append(('reason', '=', f['reason']))
        if self._int(f.get('doctor_id')):
            dom.append(('doctor', '=', self._int(f['doctor_id'])))
        if self._int(f.get('patient_id')):
            dom.append(('patient', '=', self._int(f['patient_id'])))
        apps = self.env['appointment.record'].search(dom)

        total = len(apps)
        completed = len(apps.filtered(lambda a: a.status == 'completed'))
        cancelled = len(apps.filtered(lambda a: a.status == 'cancelled'))
        cancel_rate = round(100.0 * cancelled / total) if total else 0
        attendance = round(100.0 * completed / (completed + cancelled)) if (completed + cancelled) else 0

        reason_labels = self._sel_map('appointment.record', 'reason')
        reason_counts = {}
        for a in apps:
            reason_counts[a.reason] = reason_counts.get(a.reason, 0) + 1
        reason_items = sorted(reason_counts.items(), key=lambda i: -i[1])[:8]

        status_labels = self._sel_map('appointment.record', 'status')
        status_counts = {}
        for a in apps:
            status_counts[a.status] = status_counts.get(a.status, 0) + 1
        status_keys = [k for k, __ in self._sel('appointment.record', 'status') if status_counts.get(k)]
        status_colors = {'scheduled': PALETTE[0], 'confirmed': PALETTE[1],
                         'in_progress': PALETTE[2], 'completed': GOOD, 'cancelled': CRIT}

        span_days = (dto - dfrom).days
        if span_days <= 45:
            keys = [dfrom + relativedelta(days=i) for i in range(span_days + 1)]
            counts = {k: 0 for k in keys}
            for a in apps:
                if a.date and dfrom <= a.date.date() <= dto:
                    counts[a.date.date()] += 1
            trend_title = _("Appointments per day")
            trend_labels = [format_date(self.env, k, date_format='dd/MM') for k in keys]
            trend_data = [counts[k] for k in keys]
        else:
            months = self._months(dfrom, dto)
            counts = {(m.year, m.month): 0 for m in months}
            for a in apps:
                if a.date and (a.date.year, a.date.month) in counts:
                    counts[(a.date.year, a.date.month)] += 1
            trend_title = _("Appointments per month")
            trend_labels = [self._mlabel(m) for m in months]
            trend_data = [counts[(m.year, m.month)] for m in months]

        recent = apps.sorted(key=lambda a: a.date or False, reverse=True)[:10]

        return {
            'kpis': [
                [_("Appointments"), str(total)],
                [_("Completed"), str(completed)],
                [_("Cancellation Rate"), f"{cancel_rate}%"],
                [_("Attendance Rate"), f"{attendance}%"],
            ],
            'charts': [
                {'type': 'bar', 'title': _("Appointments by reason"),
                 'labels': [reason_labels[k] for k, __ in reason_items],
                 'data': [v for __, v in reason_items], 'colors': [BLUE]},
                {'type': 'doughnut', 'title': _("Appointments by status"),
                 'labels': [status_labels[k] for k in status_keys],
                 'data': self._pcts([status_counts[k] for k in status_keys]),
                 'colors': [status_colors.get(k, BLUE) for k in status_keys]},
                {'type': 'line', 'title': trend_title,
                 'labels': trend_labels, 'data': trend_data, 'colors': [BLUE]},
            ],
            'table': {
                'cols': [_("Date"), _("Patient"), _("Reason"), _("Doctor"), _("Status"), _("Net Total")],
                'rows': [[format_datetime(self.env, a.date) if a.date else '-',
                          a.patient.name or '', reason_labels.get(a.reason, ''),
                          a.doctor.name or '-', status_labels.get(a.status, ''),
                          self._money(a.net_total)] for a in recent],
            },
        }

    # ------------------------------------------------------------------
    # 5. Finance / treasury
    # ------------------------------------------------------------------
    def _dash_finance(self, f, dfrom, dto):
        _ = self.env._
        doctor_id = self._int(f.get('doctor_id'))
        patient_id = self._int(f.get('patient_id'))

        paydom = self._dom_dt('create_date', dfrom, dto)
        if doctor_id:
            paydom.append(('doctor', '=', doctor_id))
        if patient_id:
            paydom.append(('patient', '=', patient_id))
        pays = self.env['patient.payment'].search(paydom)
        collected = sum(pays.mapped('amount'))

        appdom = self._dom_dt('date', dfrom, dto) + [('status', '!=', 'cancelled')]
        if doctor_id:
            appdom.append(('doctor', '=', doctor_id))
        if patient_id:
            appdom.append(('patient', '=', patient_id))
        apps = self.env['appointment.record'].search(appdom)
        invoiced = sum(apps.mapped('net_total'))
        billed = apps.filtered(lambda a: a.net_total > 0)
        basket = invoiced / len(billed) if billed else 0.0
        unpaid_sum = sum(a.balance_payments for a in apps if a.balance_payments > 0)

        expdom = self._dom_dt('Date', dfrom, dto) + [('status', '=', 'validated')]
        exps = self.env['expense.record'].search(expdom)
        exp_total = sum(exps.mapped('amount'))

        months = self._months(dfrom, dto)
        pay_m = {(m.year, m.month): 0.0 for m in months}
        exp_m = {(m.year, m.month): 0.0 for m in months}
        for p in pays:
            if p.create_date and (p.create_date.year, p.create_date.month) in pay_m:
                pay_m[(p.create_date.year, p.create_date.month)] += p.amount
        for e in exps:
            if e.Date and (e.Date.year, e.Date.month) in exp_m:
                exp_m[(e.Date.year, e.Date.month)] += e.amount

        paid = partial = unpaid_c = 0
        for a in billed:
            if a.balance_payments <= 0:
                paid += 1
            elif a.total_payments > 0:
                partial += 1
            else:
                unpaid_c += 1

        type_amounts = {}
        for e in exps:
            key = e.type.name or _("Uncategorized")
            type_amounts[key] = type_amounts.get(key, 0.0) + e.amount
        type_items = sorted(type_amounts.items(), key=lambda i: -i[1])[:8]

        per_patient = {}
        for a in apps:
            if a.balance_payments <= 0:
                continue
            rec = per_patient.setdefault(a.patient.id, {
                'name': a.patient.name or '', 'net': 0.0, 'paid': 0.0, 'due': 0.0})
            rec['net'] += a.net_total
            rec['paid'] += a.total_payments
            rec['due'] += a.balance_payments
        due_rows = sorted(per_patient.values(), key=lambda r: -r['due'])[:10]

        return {
            'kpis': [
                [_("Collected"), self._money(collected)],
                [_("Invoiced"), self._money(invoiced)],
                [_("Expenses"), self._money(exp_total)],
                [_("Net Balance"), self._money(collected - exp_total)],
                [_("Average Basket"), self._money(basket)],
                [_("Patient Unpaid"), self._money(unpaid_sum)],
            ],
            'charts': [
                {'type': 'line', 'title': _("Collected vs expenses (DA)"),
                 'multi': True, 'mlabels': [_("Collected"), _("Expenses")],
                 'labels': [self._mlabel(m) for m in months],
                 'data': [[round(pay_m[(m.year, m.month)]) for m in months],
                          [round(exp_m[(m.year, m.month)]) for m in months]],
                 'colors': [BLUE, CORAL]},
                {'type': 'doughnut', 'title': _("Payment status"),
                 'labels': [_("Paid"), _("Partial"), _("Unpaid")],
                 'data': self._pcts([paid, partial, unpaid_c]),
                 'colors': [GOOD, WARN, CRIT]},
                {'type': 'bar', 'title': _("Expenses by type (DA)"),
                 'labels': [i[0] for i in type_items],
                 'data': [round(i[1]) for i in type_items], 'colors': [BLUE]},
            ],
            'table': {
                'cols': [_("Patient"), _("Net Total"), _("Paid"), _("Balance Due")],
                'rows': [[r['name'], self._money(r['net']), self._money(r['paid']),
                          self._money(r['due'])] for r in due_rows],
            },
        }

    # ------------------------------------------------------------------
    # 6. Purchases & suppliers
    # ------------------------------------------------------------------
    def _dash_purchases(self, f, dfrom, dto):
        _ = self.env._
        dom = self._dom_dt('order_date', dfrom, dto)
        if self._int(f.get('supplier_id')):
            dom.append(('supplier_id', '=', self._int(f['supplier_id'])))
        if self._int(f.get('product_id')):
            dom.append(('line_ids.product', '=', self._int(f['product_id'])))
        orders = self.env['purchase.order.record'].search(dom)

        active = orders.filtered(lambda o: o.status != 'cancelled')
        total = sum(active.mapped('total'))
        in_progress = len(orders.filtered(lambda o: o.status in ('draft', 'confirmed')))
        today = date.today()
        late = len(orders.filtered(lambda o: o.status == 'confirmed'
                                   and o.expected_date and o.expected_date < today))

        sup_amounts = {}
        for o in active:
            key = o.supplier_id.name or '?'
            sup_amounts[key] = sup_amounts.get(key, 0.0) + o.total
        sup_items = sorted(sup_amounts.items(), key=lambda i: -i[1])[:8]

        status_labels = self._sel_map('purchase.order.record', 'status')
        status_counts = {}
        for o in orders:
            status_counts[o.status] = status_counts.get(o.status, 0) + 1
        status_keys = [k for k, __ in self._sel('purchase.order.record', 'status') if status_counts.get(k)]
        status_colors = {'draft': PALETTE[0], 'confirmed': PALETTE[1],
                         'received': GOOD, 'cancelled': CRIT}

        months = self._months(dfrom, dto)
        month_amounts = {(m.year, m.month): 0.0 for m in months}
        for o in active:
            if o.order_date and (o.order_date.year, o.order_date.month) in month_amounts:
                month_amounts[(o.order_date.year, o.order_date.month)] += o.total

        pay_labels = self._sel_map('purchase.order.record', 'payment_status')
        recent = orders.sorted(key=lambda o: o.order_date or False, reverse=True)[:10]

        return {
            'kpis': [
                [_("Orders"), str(len(orders))],
                [_("Total Purchases"), self._money(total)],
                [_("In Progress"), str(in_progress)],
                [_("Late"), str(late)],
            ],
            'charts': [
                {'type': 'bar', 'title': _("Spending by supplier (DA)"),
                 'labels': [i[0] for i in sup_items],
                 'data': [round(i[1]) for i in sup_items], 'colors': [BLUE]},
                {'type': 'doughnut', 'title': _("Orders by status"),
                 'labels': [status_labels[k] for k in status_keys],
                 'data': self._pcts([status_counts[k] for k in status_keys]),
                 'colors': [status_colors.get(k, BLUE) for k in status_keys]},
                {'type': 'line', 'title': _("Monthly purchases (DA)"),
                 'labels': [self._mlabel(m) for m in months],
                 'data': [round(month_amounts[(m.year, m.month)]) for m in months],
                 'colors': [BLUE]},
            ],
            'table': {
                'cols': [_("Reference"), _("Supplier"), _("Total"), _("Status"),
                         _("Payment"), _("Expected Date")],
                'rows': [[o.name or '', o.supplier_id.name or '', self._money(o.total),
                          status_labels.get(o.status, ''), pay_labels.get(o.payment_status, ''),
                          format_date(self.env, o.expected_date) if o.expected_date else '-']
                         for o in recent],
            },
        }

    # ------------------------------------------------------------------
    # 7. Stock & inventory
    # ------------------------------------------------------------------
    def _dash_stock(self, f, dfrom, dto):
        _ = self.env._
        dom = []
        if self._int(f.get('category_id')):
            dom.append(('category_id', '=', self._int(f['category_id'])))
        if f.get('availability'):
            dom.append(('availability', '=', f['availability']))
        prods = self.env['product.record'].search(dom)

        available = prods.filtered(lambda p: p.availability == 'available')
        low = prods.filtered(lambda p: p.availability == 'low_stock')
        out = prods.filtered(lambda p: p.availability == 'out_of_stock')

        top = prods.sorted(key=lambda p: -p.remaining_qt)[:10]

        avail_labels = self._sel_map('product.record', 'availability')

        cat_qty = {}
        for p in prods:
            key = p.category_id.name or _("Uncategorized")
            cat_qty[key] = cat_qty.get(key, 0) + p.remaining_qt
        cat_items = sorted(cat_qty.items(), key=lambda i: -i[1])[:8]

        alerts = (low + out).sorted(key=lambda p: p.remaining_qt)[:15]

        return {
            'kpis': [
                [_("References"), str(len(prods))],
                [_("Available"), str(len(available))],
                [_("Low Stock"), str(len(low))],
                [_("Out of Stock"), str(len(out))],
            ],
            'charts': [
                {'type': 'bar', 'title': _("Quantity by product (top 10)"),
                 'labels': [p.name for p in top],
                 'data': [p.remaining_qt for p in top], 'colors': [BLUE]},
                {'type': 'doughnut', 'title': _("Availability"),
                 'labels': [avail_labels['available'], avail_labels['low_stock'],
                            avail_labels['out_of_stock']],
                 'data': self._pcts([len(available), len(low), len(out)]),
                 'colors': [GOOD, WARN, CRIT]},
                {'type': 'bar', 'title': _("Quantity by category"),
                 'labels': [i[0] for i in cat_items],
                 'data': [i[1] for i in cat_items], 'colors': [BLUE]},
            ],
            'table': {
                'cols': [_("Product"), _("Category"), _("Quantity"), _("Minimum"), _("Availability")],
                'rows': [[p.name, p.category_id.name or '-', str(p.remaining_qt), str(p.min),
                          avail_labels.get(p.availability, '')] for p in alerts],
            },
        }

    # ------------------------------------------------------------------
    # 8. Expenses
    # ------------------------------------------------------------------
    def _dash_expenses(self, f, dfrom, dto):
        _ = self.env._
        dom = self._dom_dt('Date', dfrom, dto)
        if self._int(f.get('expense_type_id')):
            dom.append(('type', '=', self._int(f['expense_type_id'])))
        if f.get('status'):
            dom.append(('status', '=', f['status']))
        exps = self.env['expense.record'].search(dom)

        validated = exps.filtered(lambda e: e.status == 'validated')
        draft = exps.filtered(lambda e: e.status == 'draft')
        refused = exps.filtered(lambda e: e.status == 'refused')

        type_amounts = {}
        for e in exps:
            key = e.type.name or _("Uncategorized")
            type_amounts[key] = type_amounts.get(key, 0.0) + e.amount
        type_items = sorted(type_amounts.items(), key=lambda i: -i[1])[:8]

        months = self._months(dfrom, dto)
        month_amounts = {(m.year, m.month): 0.0 for m in months}
        for e in exps:
            if e.Date and (e.Date.year, e.Date.month) in month_amounts:
                month_amounts[(e.Date.year, e.Date.month)] += e.amount

        status_labels = self._sel_map('expense.record', 'status')
        recent = exps.sorted(key=lambda e: e.Date or False, reverse=True)[:10]

        return {
            'kpis': [
                [_("Validated Total"), self._money(sum(validated.mapped('amount')))],
                [_("Validated"), str(len(validated))],
                [_("Pending"), str(len(draft))],
                [_("Refused"), str(len(refused))],
            ],
            'charts': [
                {'type': 'doughnut', 'title': _("Expenses by type"),
                 'labels': [i[0] for i in type_items],
                 'data': self._pcts([i[1] for i in type_items]),
                 'colors': PALETTE},
                {'type': 'bar', 'title': _("Monthly expenses (DA)"),
                 'labels': [self._mlabel(m) for m in months],
                 'data': [round(month_amounts[(m.year, m.month)]) for m in months],
                 'colors': [BLUE]},
                {'type': 'doughnut', 'title': _("Expenses by status"),
                 'labels': [status_labels['validated'], status_labels['refused'],
                            status_labels['draft']],
                 'data': self._pcts([len(validated), len(refused), len(draft)]),
                 'colors': [GOOD, CRIT, WARN]},
            ],
            'table': {
                'cols': [_("Reference"), _("Date"), _("Expense Type"), _("Amount"), _("Status")],
                'rows': [[e.name or '', format_datetime(self.env, e.Date) if e.Date else '-',
                          e.type.name or '-', self._money(e.amount),
                          status_labels.get(e.status, '')] for e in recent],
            },
        }
