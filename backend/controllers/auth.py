from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from controllers.database import db
from controllers.models import Admin, Patient, Doctor

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/patient/register", methods=["POST"])
def patient_register():
    data = request.json

    if Patient.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already exists"}), 400

    patient = Patient(
        name=data["name"],
        email=data["email"],
        contact=data["contact"],
        password=generate_password_hash(data["password"]),
        age=data.get("age", 0),
        gender=data.get("gender", "Unknown")
    )

    db.session.add(patient)
    db.session.commit()

    return jsonify({"message": "Patient registered successfully"}), 201

@auth_bp.route("/patient/login", methods=["POST"])
def patient_login():
    data = request.json
    patient = Patient.query.filter_by(email=data["email"]).first()

    if not patient or not check_password_hash(patient.password, data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    if patient.is_blacklisted:
        return jsonify({"message": "Patient is blacklisted"}), 403

    token = create_access_token(
        identity=str(patient.id),
        additional_claims={"role": "patient"}
    )

    return jsonify({
        "access_token": token,
        "role": "patient"
    })

@auth_bp.route("/doctor/login", methods=["POST"])
def doctor_login():
    data = request.json
    doctor = Doctor.query.filter_by(email=data["email"]).first()

    if not doctor or not check_password_hash(doctor.password, data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    if doctor.is_blacklisted:
        return jsonify({"message": "Doctor is blacklisted"}), 403

    token = create_access_token(
        identity=str(doctor.id),
        additional_claims={"role": "doctor"}
    )

    return jsonify({
        "access_token": token,
        "role": "doctor"
    })

@auth_bp.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400
    admin = Admin.query.filter_by(username=username).first()


    if not admin:
        if username.lower() == "admin" and password.lower() == "admin123":
            admin = Admin(username="admin", password=generate_password_hash("admin123"))
            db.session.add(admin)
            db.session.commit()
        else:
            return jsonify({"message": "Invalid admin credentials"}), 401

    

    if not admin or not check_password_hash(admin.password, data["password"]):
        return jsonify({"message": "Invalid admin credentials"}), 401

    token = create_access_token(
        identity=str(admin.id),
        additional_claims={"role": "admin"}
    )

    return jsonify({
        "access_token": token,
        "role": "admin"
    })

