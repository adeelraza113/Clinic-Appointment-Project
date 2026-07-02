from django.urls import path
from .views import clinic_dashboard_view, register_new_patient, create_appointment_slot

urlpatterns = [
    path('', clinic_dashboard_view, name='dashboard_url'),
    path('patient/new/', register_new_patient, name='create_patient_url'),
    path('booking/schedule/', create_appointment_slot, name='book_slot_url'),
]