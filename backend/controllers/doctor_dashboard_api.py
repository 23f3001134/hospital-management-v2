from datetime import datetime
from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from controllers.models import (
    db,
    Doctor,
    Patient,
    Appointment,
    MedicalRecord,
    DoctorAvailability
)
from controllers.cache_utils import (
    get_or_set,
    delete_keys,
    key_doctor_dashboard,
    key_doctor_availability,
    key_patient_records,
    key_patient_doctor_availability
)


class DoctorDashboardAPI(Resource):

    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Doctor only"}, 403

        cache_key = key_doctor_dashboard(user_id)

        def build():
            doctor = Doctor.query.get_or_404(user_id)

            appointments = (
                db.session.query(Appointment, Patient)
                .join(Patient, Appointment.patient_id == Patient.id)
                .filter(Appointment.doctor_id == user_id)
                .filter(Appointment.status == "Scheduled")
                .order_by(Appointment.appointment_date, Appointment.appointment_time)
                .all()
            )

            upcoming_appointments = [
                {
                    "id": a.id,
                    "patient_id": p.id,
                    "patient_name": p.name,
                    "date": a.appointment_date.strftime("%Y-%m-%d"),
                    "time": a.appointment_time.strftime("%H:%M"),
                    "status": a.status
                }
                for a, p in appointments
            ]

            patients = (
                db.session.query(Patient)
                .join(Appointment, Appointment.patient_id == Patient.id)
                .filter(Appointment.doctor_id == user_id)
                .distinct()
                .order_by(Patient.name)
                .all()
            )

            assigned_patients = [
                {
                    "id": p.id,
                    "name": p.name,
                    "email": p.email,
                    "contact": p.contact
                }
                for p in patients
            ]

            records = (
                db.session.query(MedicalRecord, Patient)
                .join(Patient, MedicalRecord.patient_id == Patient.id)
                .filter(MedicalRecord.doctor_id == user_id)
                .order_by(MedicalRecord.record_date.desc())
                .limit(25)
                .all()
            )

            history = [
                {
                    "id": r.id,
                    "patient_id": p.id,
                    "patient_name": p.name,
                    "visit_type": r.visit_type,
                    "diagnosis": r.diagnosis,
                    "prescription": r.prescription,
                    "medicine": r.medicine,
                    "record_date": r.record_date.strftime("%Y-%m-%d")
                }
                for r, p in records
            ]

            availability = DoctorAvailability.query.filter_by(
                doctor_id=user_id
            ).order_by(DoctorAvailability.date).all()

            availability_data = [
                {
                    "date": a.date.strftime("%Y-%m-%d"),
                    "morning_slot": a.morning_slot,
                    "evening_slot": a.evening_slot
                }
                for a in availability
            ]

            return {
                "doctor": {
                    "id": doctor.id,
                    "name": doctor.doctor_name,
                    "department": doctor.department,
                    "email": doctor.email,
                    "contact": doctor.contact,
                    "experience": doctor.experience
                },
                "upcoming_appointments": upcoming_appointments,
                "assigned_patients": assigned_patients,
                "history": history,
                "availability": availability_data
            }, 200

        return get_or_set(cache_key, build)


class DoctorAvailabilityAPI(Resource):

    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Doctor only"}, 403

        cache_key = key_doctor_availability(user_id)

        def build():
            availability = DoctorAvailability.query.filter_by(
                doctor_id=user_id
            ).order_by(DoctorAvailability.date).all()

            return [
                {
                    "date": a.date.strftime("%Y-%m-%d"),
                    "morning_slot": a.morning_slot,
                    "evening_slot": a.evening_slot
                }
                for a in availability
            ], 200

        return get_or_set(cache_key, build)

    @jwt_required()
    def put(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Doctor only"}, 403

        data = request.get_json() or []
        if not isinstance(data, list):
            return {"message": "Availability must be a list"}, 400

        DoctorAvailability.query.filter_by(doctor_id=user_id).delete()

        for slot in data:
            date_str = slot.get("date")
            morning = slot.get("morning_slot")
            evening = slot.get("evening_slot")
            if not date_str or not morning or not evening:
                return {"message": "date, morning_slot, evening_slot required"}, 400

            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

            db.session.add(DoctorAvailability(
                doctor_id=user_id,
                date=date_obj,
                morning_slot=morning,
                evening_slot=evening
            ))

        db.session.commit()
        delete_keys(
            key_doctor_availability(user_id),
            key_doctor_dashboard(user_id),
            key_patient_doctor_availability(user_id)
        )
        return {"message": "Availability updated"}, 200

class PatientHistoryAPI(Resource):

    @jwt_required()
    def get(self, patient_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Doctor only"}, 403

        records = (
            db.session.query(MedicalRecord)
            .filter(
                MedicalRecord.doctor_id == user_id,
                MedicalRecord.patient_id == patient_id
            )
            .order_by(MedicalRecord.record_date.desc())
            .all()
        )

        history = [
            {
                "id": r.id,
                "visit_type": r.visit_type,
                "diagnosis": r.diagnosis,
                "prescription": r.prescription,
                "medicine": r.medicine,
                "record_date": r.record_date.strftime("%Y-%m-%d")
            }
            for r in records
        ]

        return {"patient_id": patient_id, "history": history}, 200
    @jwt_required()
    def post(self, patient_id): 
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Doctor only"}, 403

        data = request.get_json()
        visit_type = data.get("visit_type")
        diagnosis = data.get("diagnosis")
        prescription = data.get("prescription")
        medicine = data.get("medicine")

        if not all([visit_type, diagnosis, prescription, medicine]):
            return {"message": "All fields are required"}, 400

        new_record = MedicalRecord(
            doctor_id=user_id,
            patient_id=patient_id,
            visit_type=visit_type,
            diagnosis=diagnosis,
            prescription=prescription,
            medicine=medicine,
            record_date=datetime.utcnow().date()
        )

        db.session.add(new_record)
        db.session.commit()

        delete_keys(
            key_doctor_dashboard(user_id),
            key_patient_records(patient_id)
        )
        return {"message": "Medical record added", "record_id": new_record.id}, 201
    @jwt_required()
    def put(self, record_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Doctor only"}, 403

        record = MedicalRecord.query.get_or_404(record_id)

        if record.doctor_id != user_id:
            return {"message": "Unauthorized"}, 403

        data = request.get_json()
        record.visit_type = data.get("visit_type", record.visit_type)
        record.diagnosis = data.get("diagnosis", record.diagnosis)
        record.prescription = data.get("prescription", record.prescription)
        record.medicine = data.get("medicine", record.medicine)

        db.session.commit()

        delete_keys(
            key_doctor_dashboard(user_id),
            key_patient_records(record.patient_id)
        )
        return {"message": "Medical record updated"}, 200
    
