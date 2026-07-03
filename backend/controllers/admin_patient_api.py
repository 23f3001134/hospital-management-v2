from flask_restful import Resource
from flask import request
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.security import generate_password_hash

from controllers.models import db, Patient, MedicalRecord, Doctor
from controllers.cache_utils import (
    delete_keys,
    key_admin_dashboard,
    key_patient_dashboard,
    key_patient_records
)


class AdminPatientDetailAPI(Resource):

    @jwt_required()
    def get(self, patient_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        patient = Patient.query.get_or_404(patient_id)
        return {
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "contact": patient.contact,
            "age": patient.age,
            "gender": patient.gender,
            "is_blacklisted": patient.is_blacklisted
        }, 200

    @jwt_required()
    def put(self, patient_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        patient = Patient.query.get_or_404(patient_id)
        data = request.get_json() or {}

        if "email" in data and data["email"] != patient.email:
            if Patient.query.filter_by(email=data["email"]).first():
                return {"message": "Email already exists"}, 400

        if "contact" in data and data["contact"] != patient.contact:
            if Patient.query.filter_by(contact=data["contact"]).first():
                return {"message": "Contact already exists"}, 400

        patient.name = data.get("name", patient.name)
        patient.email = data.get("email", patient.email)
        patient.contact = data.get("contact", patient.contact)
        patient.age = data.get("age", patient.age)
        patient.gender = data.get("gender", patient.gender)

        if "password" in data and data["password"]:
            patient.password = generate_password_hash(data["password"])

        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_patient_dashboard(patient_id),
            key_patient_records(patient_id)
        )
        return {"message": "Patient updated successfully"}, 200

    @jwt_required()
    def delete(self, patient_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        patient = Patient.query.get_or_404(patient_id)
        db.session.delete(patient)
        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_patient_dashboard(patient_id),
            key_patient_records(patient_id)
        )
        return {"message": "Patient deleted successfully"}, 200


class AdminPatientRecordsAPI(Resource):

    @jwt_required()
    def get(self, patient_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        records = (
            db.session.query(MedicalRecord, Doctor)
            .join(Doctor, MedicalRecord.doctor_id == Doctor.id)
            .filter(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.record_date.desc())
            .all()
        )

        return [
            {
                "id": r.id,
                "doctor_name": d.doctor_name,
                "visit_type": r.visit_type,
                "diagnosis": r.diagnosis,
                "prescription": r.prescription,
                "medicine": r.medicine,
                "record_date": r.record_date.strftime("%Y-%m-%d")
            }
            for r, d in records
        ], 200


class AdminPatientBlacklistAPI(Resource):

    @jwt_required()
    def put(self, patient_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        patient = Patient.query.get_or_404(patient_id)
        data = request.get_json() or {}
        if "is_blacklisted" in data:
            patient.is_blacklisted = bool(data["is_blacklisted"])
        else:
            patient.is_blacklisted = not patient.is_blacklisted

        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_patient_dashboard(patient_id),
            key_patient_records(patient_id)
        )
        return {
            "message": "Patient blacklist updated",
            "is_blacklisted": patient.is_blacklisted
        }, 200
