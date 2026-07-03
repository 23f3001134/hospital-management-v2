from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import request
from controllers.models import db, MedicalRecord, Patient
from controllers.cache_utils import delete_keys, key_doctor_dashboard, key_patient_records


class MedicalRecordAPI(Resource):

    @jwt_required()
    def get(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Only doctors can view records"}, 403
        patient_id = request.args.get("patient_id", type=int)

        query = (
            db.session.query(MedicalRecord, Patient)
            .join(Patient, MedicalRecord.patient_id == Patient.id)
            .filter(MedicalRecord.doctor_id == user_id)
            .order_by(MedicalRecord.record_date.desc())
        )

        if patient_id:
            query = query.filter(MedicalRecord.patient_id == patient_id)

        records = query.all()

        return [
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
        ], 200

    @jwt_required()
    def post(self):
        user_id = int(get_jwt_identity())
        role = get_jwt().get("role")

        if role != "doctor":
            return {"message": "Only doctors can add records"}, 403

        data = request.get_json()

        record = MedicalRecord(
            patient_id=data["patient_id"],
            doctor_id=user_id,
            visit_type=data.get("visit_type", "In-person"),
            diagnosis=data["diagnosis"],
            prescription=data["prescription"],
            medicine=data["medicine"]
        )

        db.session.add(record)
        db.session.commit()
        delete_keys(
            key_doctor_dashboard(user_id),
            key_patient_records(data["patient_id"])
        )
        return {"message": "Medical record added"}, 201
