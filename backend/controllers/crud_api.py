from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import request
from controllers.models import db, Patient, Doctor
from werkzeug.security import generate_password_hash
from controllers.cache_utils import (
    delete_keys,
    key_admin_dashboard,
    key_patient_dashboard,
    key_patient_records,
    key_doctor_dashboard,
    key_patient_department_doctors
)

class PatientProfileAPI(Resource):

    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "patient":
            return {"message": "Unauthorized"}, 403

        patient = Patient.query.get_or_404(user_id)

        return {
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "contact": patient.contact,
            "age": patient.age,
            "gender": patient.gender
        }, 200

    @jwt_required()
    def put(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "patient":
            return {"message": "Unauthorized"}, 403

        patient = Patient.query.get_or_404(user_id)
        data = request.get_json()

        patient.name = data.get("name", patient.name)
        patient.contact = data.get("contact", patient.contact)
        patient.age = data.get("age", patient.age)
        patient.gender = data.get("gender", patient.gender)

        if "password" in data:
            patient.password = generate_password_hash(data["password"])

        db.session.commit()
        delete_keys(
            key_patient_dashboard(user_id),
            key_patient_records(user_id),
            key_admin_dashboard("")
        )
        return {"message": "Profile updated successfully"}, 200


class DoctorCRUDAPI(Resource):

    @jwt_required()
    def get(self):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        doctors = Doctor.query.all()
        return [
            {
                "id": d.id,
                "doctor_name": d.doctor_name,
                "department": d.department,
                "experience": d.experience,
                "email": d.email,
                "contact": d.contact
            }
            for d in doctors
        ], 200

    @jwt_required()
    def post(self):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        data = request.get_json()

        required = ["doctor_name", "department", "experience", "email", "contact"]
        for f in required:
            if not data.get(f):
                return {"message": f"{f} is required"}, 400

        if Doctor.query.filter_by(email=data["email"]).first():
            return {"message": "Email already exists"}, 400

        doctor = Doctor(
            doctor_name=data["doctor_name"],
            department=data["department"],
            experience=int(data["experience"]),
            email=data["email"],
            contact=data["contact"],
            password=generate_password_hash("doctor123")
        )

        db.session.add(doctor)
        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_patient_department_doctors(doctor.department)
        )
        return {"message": "Doctor added successfully"}, 201

class DoctorPasswordResetAPI(Resource):

    @jwt_required()
    def post(self, doctor_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        doctor = Doctor.query.get_or_404(doctor_id)
        doctor.password = generate_password_hash("doctor123")
        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_doctor_dashboard(doctor_id)
        )
        return {"message": "Doctor password reset to doctor123"}, 200


class DoctorDetailAPI(Resource):

    @jwt_required()
    def put(self, doctor_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        doctor = Doctor.query.get_or_404(doctor_id)
        data = request.get_json() or {}

        if "email" in data and data["email"] != doctor.email:
            if Doctor.query.filter_by(email=data["email"]).first():
                return {"message": "Email already exists"}, 400

        if "contact" in data and data["contact"] != doctor.contact:
            if Doctor.query.filter_by(contact=data["contact"]).first():
                return {"message": "Contact already exists"}, 400

        doctor.doctor_name = data.get("doctor_name", doctor.doctor_name)
        doctor.department = data.get("department", doctor.department)
        doctor.experience = int(data.get("experience", doctor.experience))
        doctor.email = data.get("email", doctor.email)
        doctor.contact = data.get("contact", doctor.contact)

        if "password" in data and data["password"]:
            doctor.password = generate_password_hash(data["password"])

        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_doctor_dashboard(doctor_id),
            key_patient_department_doctors(doctor.department)
        )
        return {"message": "Doctor updated successfully"}, 200

    @jwt_required()
    def delete(self, doctor_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        doctor = Doctor.query.get_or_404(doctor_id)
        db.session.delete(doctor)
        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_doctor_dashboard(doctor_id),
            key_patient_department_doctors(doctor.department)
        )
        return {"message": "Doctor deleted successfully"}, 200


class DoctorBlacklistAPI(Resource):

    @jwt_required()
    def put(self, doctor_id):
        role = get_jwt().get("role")
        if role != "admin":
            return {"message": "Admin only"}, 403

        doctor = Doctor.query.get_or_404(doctor_id)
        data = request.get_json() or {}
        if "is_blacklisted" in data:
            doctor.is_blacklisted = bool(data["is_blacklisted"])
        else:
            doctor.is_blacklisted = not doctor.is_blacklisted

        db.session.commit()
        delete_keys(
            key_admin_dashboard(""),
            key_doctor_dashboard(doctor_id),
            key_patient_department_doctors(doctor.department)
        )
        return {
            "message": "Doctor blacklist updated",
            "is_blacklisted": doctor.is_blacklisted
        }, 200
