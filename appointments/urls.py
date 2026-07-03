from django.urls import path
from .views import (
    clinic_dashboard_view,create_appointment_slot, alter_booking_status, doctor_onboarding_view,
    patient_signup_view, global_login_view, global_logout_view,
    add_clinical_summary_view, view_invoice_view
)

urlpatterns = [
    path('', clinic_dashboard_view, name='dashboard_url'),
    path('auth/login/', global_login_view, name='login_url'),
    path('auth/signup/', patient_signup_view, name='signup_url'),
    path('auth/logout/', global_logout_view, name='logout_url'),
    path('booking/schedule/', create_appointment_slot, name='book_slot_url'),
    path('booking/alter/<int:slot_id>/<str:target_action>/', alter_booking_status, name='alter_status_url'),
    path('booking/treat/<int:slot_id>/', add_clinical_summary_view, name='add_prescription_url'),
    path('booking/invoice/<int:slot_id>/', view_invoice_view, name='view_invoice_url'),
    path('management/onboard-doctor/', doctor_onboarding_view, name='onboard_doctor_url'),
    
]