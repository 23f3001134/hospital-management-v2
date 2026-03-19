import { createRouter, createWebHistory } from "vue-router";

import Home from "../views/Home.vue";
import PatientRegister from "../views/PatientRegister.vue";
import PatientLogin from "../views/PatientLogin.vue";
import DoctorLogin from "../views/DoctorLogin.vue";
import AdminLogin from "../views/AdminLogin.vue";

import PatientDashboard from "../views/PatientDashboard.vue";
import DoctorDashboard from "../views/DoctorDashboard.vue";
import AdminDashboard from "../views/AdminDashboard.vue";
import AddDoctor from "../views/AddDoctor.vue";
import PatientHistory from "../views/Patienthistory.vue";
import UpdatePatientHistory from "../views/UpdatePatientHistory.vue";
import DoctorAvailiabilty from "../views/DoctorAvailiabilty.vue";
import ViewDetails from "../views/ViewDetails.vue";


const routes = [
  {
    path: "/", 
    name: "Home",
    component: Home
  },
  {
    path: "/patient/register",
    name: "PatientRegister",
    component: PatientRegister
  },
  {
    path: "/patient/login",
    name: "PatientLogin",
    component: PatientLogin
  },
  {
    path: "/doctor/login",
    name: "DoctorLogin",
    component: DoctorLogin
  },
  {
    path: "/admin/login",
    name: "AdminLogin",
    component: AdminLogin
  },

  {
    path: "/patient/dashboard",
    name: "PatientDashboard",
    component: PatientDashboard
  },
  {
    path: "/doctor/dashboard",
    name: "DoctorDashboard",
    component: DoctorDashboard
  },
  {
    path: "/admin/dashboard",
    name: "AdminDashboard",
    component: AdminDashboard
  },
  {
    path: "/add_doctor",
    name: "AddDoctor",
    component: AddDoctor
  },
  {
    path: "/patient/history",
    name: "PatientHistory",
    component: PatientHistory
  },
  {
    path: "/patient/departments/:department",
    name: "ViewDetails",
    component: ViewDetails,
    props: true
  },
  {
    path: "/patient/history/update",
    name: "UpdatePatientHistory",
    component: UpdatePatientHistory
  },
  {
    path: "/doctor/availability",
    name: "DoctorAvailability",
    component: DoctorAvailiabilty
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
