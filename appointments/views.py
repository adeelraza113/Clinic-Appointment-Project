from django.shortcuts import render, redirect
from django.contrib import messages
from .models import MedicalSpecialist, PatientRecord, BookingSlot

def clinic_dashboard_view(request):
    """Main panel to overview specialists, records, and book slots."""
    all_specialists = MedicalSpecialist.objects.all()
    all_records = PatientRecord.objects.all()
    active_bookings = BookingSlot.objects.all().order_by('-schedule_date')
    
    context = {
        'specialists': all_specialists,
        'patients': all_records,
        'bookings': active_bookings,
    }
    return render(request, 'dashboard.html', context)


def register_new_patient(request):
    """Saves a new patient record into MySQL."""
    if request.method == "POST":
        p_name = request.POST.get('client_name')
        p_age = request.POST.get('client_age')
        p_gender = request.POST.get('client_gender')
        p_phone = request.POST.get('client_phone')
        p_notes = request.POST.get('client_notes', '')

        if p_name and p_age and p_phone:
            PatientRecord.objects.create(
                full_name=p_name,
                age_years=p_age,
                gender_identity=p_gender,
                phone_primary=p_phone,
                health_notes=p_notes
            )
            messages.success(request, "Patient profile successfully logged!")
            return redirect('dashboard_url')
        else:
            messages.error(request, "Please enter all required fields.")
            
    return render(request, 'register_patient.html')


def create_appointment_slot(request):
    """Processes booking validation and engine storage."""
    if request.method == "POST":
        doc_id = request.POST.get('doc_selection')
        pat_id = request.POST.get('pat_selection')
        b_date = request.POST.get('booking_date')
        b_time = request.POST.get('booking_time')

        if doc_id and pat_id and b_date and b_time:
            doctor_obj = MedicalSpecialist.objects.get(id=doc_id)
            patient_obj = PatientRecord.objects.get(id=pat_id)
            
            BookingSlot.objects.create(
                assigned_doctor=doctor_obj,
                registered_patient=patient_obj,
                schedule_date=b_date,
                schedule_time=b_time
            )
            messages.success(request, "Appointment slot successfully scheduled!")
            return redirect('dashboard_url')
            
    all_specialists = MedicalSpecialist.objects.all()
    all_records = PatientRecord.objects.all()
    return render(request, 'schedule_slot.html', {'specialists': all_specialists, 'patients': all_records})

def alter_booking_status(request, slot_id, target_action):
    """Updates the execution lifecycle of a scheduled clinical slot."""
    try:
        target_slot = BookingSlot.objects.get(id=slot_id)
        if target_action in ['Completed', 'Cancelled']:
            target_slot.current_status = target_action
            target_slot.save()
            messages.success(request, f"Slot state successfully marked as {target_action}!")
    except BookingSlot.DoesNotExist:
        messages.error(request, "Requested operational slot not found.")
        
    return redirect('dashboard_url')