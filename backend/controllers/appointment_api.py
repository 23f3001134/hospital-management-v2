from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import request
from controllers.models import db, Appointment
from controllers.cache_utils import (
    delete_keys,
    key_patient_dashboard,
    key_doctor_dashboard,
    key_admin_dashboard
)
from datetime import datetime


class AppointmentAPI(Resource):

    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "patient":
            return {"message": "Only patients can book appointments"}, 403

        data = request.get_json()
        try:
            date_obj = datetime.strptime(data["appointment_date"], "%Y-%m-%d").date()
            time_obj = datetime.strptime(data["appointment_time"], "%H:%M").time()
        except (KeyError, ValueError, TypeError):
            return {"message": "Invalid appointment date/time"}, 400

        appointment = Appointment(
            patient_id=user_id,
            doctor_id=data["doctor_id"],
            appointment_date=date_obj,
            appointment_time=time_obj
        )

        db.session.add(appointment)
        db.session.commit()
        delete_keys(
            key_patient_dashboard(user_id),
            key_doctor_dashboard(data["doctor_id"]),
            key_admin_dashboard("")
        )
        return {"message": "Appointment booked successfully"}, 201


class AppointmentStatusAPI(Resource):

    @jwt_required()
    def put(self, appointment_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Only doctors can update status"}, 403

        data = request.get_json() or {}
        status = (data.get("status") or "").strip()
        if status not in {"Completed", "Cancelled"}:
            return {"message": "Invalid status"}, 400

        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.doctor_id != user_id:
            return {"message": "Unauthorized"}, 403

        appointment.status = status
        db.session.commit()
        delete_keys(
            key_doctor_dashboard(user_id),
            key_patient_dashboard(appointment.patient_id),
            key_admin_dashboard("")
        )
        return {"message": "Status updated"}, 200


class AppointmentCancelAPI(Resource):

    @jwt_required()
    def put(self, appointment_id):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "patient":
            return {"message": "Only patients can cancel"}, 403

        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.patient_id != user_id:
            return {"message": "Unauthorized"}, 403

        appointment.status = "Cancelled"
        db.session.commit()
        delete_keys(
            key_patient_dashboard(user_id),
            key_doctor_dashboard(appointment.doctor_id),
            key_admin_dashboard("")
        )
        return {"message": "Appointment cancelled"}, 200
