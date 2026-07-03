from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MedicalSpecialist, PatientRecord, BookingSlot, ClinicalPrescription, FinancialInvoice

def patient_signup_view(request):
    if request.user.is_authenticated: return redirect('dashboard_url')
    if request.method == "POST":
        u_name = request.POST.get('account_user')
        u_pass = request.POST.get('account_pass')
        p_name = request.POST.get('client_name')
        p_age = request.POST.get('client_age')
        p_gender = request.POST.get('client_gender')
        p_phone = request.POST.get('client_phone')

        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Username already registered.")
            return render(request, 'signup.html')

        if u_name and u_pass and p_name:
            new_user = User.objects.create_user(username=u_name, password=u_pass)
            PatientRecord.objects.create(user_auth=new_user, full_name=p_name, age_years=p_age, gender_identity=p_gender, phone_primary=p_phone)
            login(request, new_user)
            return redirect('dashboard_url')
    return render(request, 'signup.html')


def global_login_view(request):
    if request.user.is_authenticated: return redirect('dashboard_url')
    if request.method == "POST":
        u_name = request.POST.get('input_user')
        u_pass = request.POST.get('input_pass')
        user = authenticate(request, username=u_name, password=u_pass)
        if user is not None:
            login(request, user)
            return redirect('dashboard_url')
        messages.error(request, "Invalid security credentials.")
    return render(request, 'login.html')


def global_logout_view(request):
    logout(request)
    return redirect('login_url')


@login_required(login_url='login_url')
def clinic_dashboard_view(request):
    """Enterprise multi-tenant dashboard rendering views based on specialized roles."""
    is_staff = request.user.is_superuser or request.user.is_staff
    is_doctor = hasattr(request.user, 'medicalspecialist')
    is_patient = hasattr(request.user, 'patientrecord')

    if is_staff:
        active_bookings = BookingSlot.objects.all().order_by('-schedule_date')
    elif is_doctor:
        # Doctor views ONLY their assigned patient slots
        current_doctor = request.user.medicalspecialist
        active_bookings = BookingSlot.objects.filter(assigned_doctor=current_doctor).order_by('-schedule_date')
    elif is_patient:
        current_patient = request.user.patientrecord
        active_bookings = BookingSlot.objects.filter(registered_patient=current_patient).order_by('-schedule_date')
    else:
        active_bookings = []

    context = {
        'bookings': active_bookings,
        'is_staff': is_staff,
        'is_doctor': is_doctor,
        'is_patient': is_patient,
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='login_url')
def create_appointment_slot(request):
    is_staff = request.user.is_superuser or request.user.is_staff
    is_patient = hasattr(request.user, 'patientrecord')

    if request.method == "POST":
        doc_id = request.POST.get('doc_selection')
        pat_id = request.POST.get('pat_selection') if is_staff else request.user.patientrecord.id
        b_date = request.POST.get('booking_date')
        b_time = request.POST.get('booking_time')

        if doc_id and pat_id and b_date and b_time:
            doctor_obj = MedicalSpecialist.objects.get(id=doc_id)
            patient_obj = PatientRecord.objects.get(id=pat_id)
            
            if BookingSlot.objects.filter(assigned_doctor=doctor_obj, schedule_date=b_date, schedule_time=b_time, current_status='Active').exists():
                messages.error(request, f"Dr. {doctor_obj.expert_name} is already booked at this time.")
                return redirect('book_slot_url')

            BookingSlot.objects.create(assigned_doctor=doctor_obj, registered_patient=patient_obj, schedule_date=b_date, schedule_time=b_time)
            messages.success(request, "Appointment slot scheduled!")
            return redirect('dashboard_url')
            
    context = {
        'specialists': MedicalSpecialist.objects.all(), 
        'patients': PatientRecord.objects.all() if is_staff else [request.user.patientrecord],
        'is_staff': is_staff
    }
    return render(request, 'schedule_slot.html', context)


@login_required(login_url='login_url')
def add_clinical_summary_view(request, slot_id):
    """Allows doctors to input prescription data and triggers automatic billing generation."""
    booking = BookingSlot.objects.get(id=slot_id)
    
    if request.method == "POST":
        symptoms = request.POST.get('symptoms')
        meds = request.POST.get('medications')
        
        ClinicalPrescription.objects.create(associated_booking=booking, symptoms_observed=symptoms, prescribed_medication=meds)
        base_fee = booking.assigned_doctor.consultation_fee
        tax = 150.00
        grand_total = base_fee + tax
        
        FinancialInvoice.objects.create(linked_booking=booking, base_consultation_fee=base_fee, healthcare_tax=tax, grand_total_payable=grand_total)
        booking.current_status = 'Completed'
        booking.save()
        
        messages.success(request, "Prescription saved and invoice generated successfully!")
        return redirect('dashboard_url')
        
    return render(request, 'add_prescription.html', {'booking': booking})


@login_required(login_url='login_url')
def view_invoice_view(request, slot_id):
    """Renders printable billing sheet for corporate processing."""
    booking = BookingSlot.objects.get(id=slot_id)
    invoice = FinancialInvoice.objects.get(linked_booking=booking)
    return render(request, 'invoice_detail.html', {'booking': booking, 'invoice': invoice})


@login_required(login_url='login_url')
def alter_booking_status(request, slot_id, target_action):
    booking = BookingSlot.objects.get(id=slot_id)
    if target_action == 'Cancelled':
        booking.current_status = 'Cancelled'
        booking.save()
        messages.success(request, "Appointment cancelled successfully.")
    return redirect('dashboard_url')

@login_required(login_url='login_url')
def doctor_onboarding_view(request):
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access Denied.")
        return redirect('dashboard_url')

    if request.method == "POST":
        u_name = request.POST.get('doc_user')
        u_pass = request.POST.get('doc_pass')
        d_name = request.POST.get('expert_name')
        d_spec = request.POST.get('specialization')
        d_fee = request.POST.get('consultation_fee')

        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Username already exists.")
            return redirect('onboard_doctor_url')

        try:
            with transaction.atomic():
                new_doc_user = User.objects.create_user(username=u_name, password=u_pass)
                MedicalSpecialist.objects.create(
                    user_auth=new_doc_user,
                    expert_name=d_name,
                    medical_specialty=d_spec,
                    consultation_fee=d_fee
                )
            messages.success(request, f"Dr. {d_name} has been securely onboarded.")
            return redirect('dashboard_url')
        except Exception as e:
            messages.error(request, "System routing error during onboarding database commit.")
            
    return render(request, 'onboard_doctor.html')

@login_required(login_url='login_url')
def view_invoice_view(request, booking_id):
    booking = get_object_or_404(BookingSlot, id=booking_id)
    is_patient = hasattr(request.user, 'patient') and booking.registered_patient == request.user.patient
    is_doctor = hasattr(request.user, 'medicalspecialist') and booking.assigned_doctor == request.user.medicalspecialist
    is_staff = request.user.is_staff or request.user.is_superuser
    
    if not (is_patient or is_doctor or is_staff):
        messages.error(request, "Unauthorized Invoice Request Access.")
        return redirect('dashboard_url')
    consultation_fee = booking.assigned_doctor.consultation_fee
    hospital_charges = 200.00  
    grand_total = float(consultation_fee) + hospital_charges
    
    context = {
        'booking': booking,
        'consultation_fee': consultation_fee,
        'hospital_charges': hospital_charges,
        'grand_total': grand_total
    }
    return render(request, 'invoice_detail.html', context)