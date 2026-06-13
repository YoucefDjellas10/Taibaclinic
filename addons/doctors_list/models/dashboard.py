from odoo import models, api
from datetime import date
import calendar

class DoctorDashboard(models.Model):
    _name = 'doctor.dashboard'
    _description = 'Doctor Dashboard'

    @api.model
    def get_dashboard_data(self, month, year):
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        first_str = f'{first_day} 00:00:00'
        last_str = f'{last_day} 23:59:59'

        doctors = self.env['doctors'].search([])
        result = []
        total_gross = total_labo = total_doctor_earn = total_clinic_earn = total_appointments = 0

        for doctor in doctors:
            appointments = self.env['appointment.record'].search([
                ('doctor', '=', doctor.id),
                ('date', '>=', first_str),
                ('date', '<=', last_str),
            ])
            total_app  = len(appointments)
            completed  = len(appointments.filtered(lambda a: a.status == 'completed'))
            in_progress= len(appointments.filtered(lambda a: a.status == 'in_progress'))
            cancelled  = len(appointments.filtered(lambda a: a.status == 'cancelled'))
            scheduled  = len(appointments.filtered(lambda a: a.status in ('scheduled', 'confirmed')))

            gross       = sum(appointments.mapped('net_total'))
            labo        = sum(appointments.mapped('total_payments_labo'))
            net         = gross - labo
            pct         = doctor.percentage or 0
            doctor_earn = round(net * pct / 100, 2)
            clinic_earn = round(net - doctor_earn, 2)

            total_gross        += gross
            total_labo         += labo
            total_doctor_earn  += doctor_earn
            total_clinic_earn  += clinic_earn
            total_appointments += total_app

            result.append({
                'id':                doctor.id,
                'name':              doctor.name,
                'speciality':        doctor.speciality.name if doctor.speciality else '',
                'percentage':        pct,
                'total_appointments':total_app,
                'completed':         completed,
                'in_progress':       in_progress,
                'cancelled':         cancelled,
                'scheduled':         scheduled,
                'gross_total':       round(gross, 2),
                'labo_total':        round(labo, 2),
                'net_revenue':       round(net, 2),
                'doctor_earnings':   doctor_earn,
                'clinic_earnings':   clinic_earn,
            })

        return {
            'doctors': sorted(result, key=lambda d: d['doctor_earnings'], reverse=True),
            'stats': {
                'total_appointments':     total_appointments,
                'total_gross':            round(total_gross, 2),
                'total_labo':             round(total_labo, 2),
                'total_net':              round(total_gross - total_labo, 2),
                'total_doctor_earnings':  round(total_doctor_earn, 2),
                'total_clinic_earnings':  round(total_clinic_earn, 2),
            },
            'month': month,
            'year':  year,
        }