import os

from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from celery import Celery
from celery.schedules import crontab
from werkzeug.security import generate_password_hash
from config import Config
from controllers.models import db, Admin
from extensions import cache
from controllers.auth import auth_bp
from controllers.crud_api import (
    DoctorCRUDAPI,
    DoctorPasswordResetAPI,
    DoctorDetailAPI,
    DoctorBlacklistAPI,
    PatientProfileAPI
)
from controllers.admin_dashboard_api import AdminDashboardAPI
from controllers.patient_dashboard_api import (
    PatientDashboardAPI,
    PatientRecordsAPI,
    PatientExportAPI
)
from controllers.patient_department_api import (
    PatientDepartmentDoctorsAPI,
    PatientDoctorAvailabilityAPI
)
from controllers.admin_patient_api import (
    AdminPatientDetailAPI,
    AdminPatientRecordsAPI,
    AdminPatientBlacklistAPI
)
from controllers.doctor_dashboard_api import DoctorDashboardAPI, DoctorAvailabilityAPI
from controllers.medicalrecord_api import MedicalRecordAPI
from controllers.appointment_api import AppointmentAPI, AppointmentStatusAPI, AppointmentCancelAPI

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

db.init_app(app)
cache.init_app(app)
JWTManager(app)

api = Api(app)

export_dir = os.path.join(app.root_path, app.config["EXPORT_DIR"])
os.makedirs(export_dir, exist_ok=True)


def make_celery(flask_app):
    celery_app = Celery(
        flask_app.import_name,
        broker=flask_app.config["CELERY_BROKER_URL"],
        backend=flask_app.config["CELERY_RESULT_BACKEND"]
    )
    celery_app.conf.update(flask_app.config)

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


celery = make_celery(app)
celery.conf.beat_schedule = {
    "daily-reminders": {
        "task": "controllers.task.send_daily_reminders",
        "schedule": crontab(
            hour=app.config["DAILY_REMINDER_HOUR"],
            minute=app.config["DAILY_REMINDER_MINUTE"]
        )
    },
    "monthly-reports": {
        "task": "controllers.task.send_monthly_activity_reports",
        "schedule": crontab(
            day_of_month=1,
            hour=app.config["MONTHLY_REPORT_HOUR"],
            minute=app.config["MONTHLY_REPORT_MINUTE"]
        )
    }
}

app.register_blueprint(auth_bp)

api.add_resource(DoctorCRUDAPI, "/admin/doctors")
api.add_resource(DoctorPasswordResetAPI, "/admin/doctors/<int:doctor_id>/reset-password")
api.add_resource(DoctorDetailAPI, "/admin/doctors/<int:doctor_id>")
api.add_resource(DoctorBlacklistAPI, "/admin/doctors/<int:doctor_id>/blacklist")
api.add_resource(AdminDashboardAPI, "/admin/dashboard")
api.add_resource(DoctorDashboardAPI, "/doctor/dashboard")
api.add_resource(DoctorAvailabilityAPI, "/doctor/availability")
api.add_resource(MedicalRecordAPI, "/doctor/records")
api.add_resource(AppointmentAPI, "/appointments")
api.add_resource(AppointmentStatusAPI, "/appointments/<int:appointment_id>/status")
api.add_resource(AppointmentCancelAPI, "/appointments/<int:appointment_id>/cancel")
api.add_resource(PatientProfileAPI, "/patient/profile")
api.add_resource(PatientDashboardAPI, "/patient/dashboard")
api.add_resource(PatientRecordsAPI, "/patient/records")
api.add_resource(PatientExportAPI, "/patient/records/export")
api.add_resource(PatientDepartmentDoctorsAPI, "/patient/departments/<string:department>/doctors")
api.add_resource(PatientDoctorAvailabilityAPI, "/patient/doctors/<int:doctor_id>/availability")
api.add_resource(AdminPatientDetailAPI, "/admin/patients/<int:patient_id>")
api.add_resource(AdminPatientRecordsAPI, "/admin/patients/<int:patient_id>/records")
api.add_resource(AdminPatientBlacklistAPI, "/admin/patients/<int:patient_id>/blacklist")


import controllers.task 

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not Admin.query.first():
            admin = Admin(
                username="admin",
                password=generate_password_hash("admin123")
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)

