from django.urls import path
from .views import (
    clinic_dashboard_view, register_new_patient, 
    create_appointment_slot, alter_booking_status,
    patient_signup_view, global_login_view, global_logout_view
)

urlpatterns = [
    path('', clinic_dashboard_view, name='dashboard_url'),
    path('auth/login/', global_login_view, name='login_url'),
    path('auth/signup/', patient_signup_view, name='signup_url'),
    path('auth/logout/', global_logout_view, name='logout_url'),
    path('patient/new/', register_new_patient, name='create_patient_url'),
    path('booking/schedule/', create_appointment_slot, name='book_slot_url'),
    path('booking/alter/<int:slot_id>/<str:target_action>/', alter_booking_status, name='alter_status_url'),
]