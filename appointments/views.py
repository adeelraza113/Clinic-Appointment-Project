from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MedicalSpecialist, PatientRecord, BookingSlot

@login_required(login_url='login_url')
def clinic_dashboard_view(request):
    """Multi-tenant unified dashboard sorting data based on operational privileges."""
    is_patient = hasattr(request.user, 'patientrecord')
    is_staff = request.user.is_superuser or request.user.is_staff

    if is_staff:
        active_bookings = BookingSlot.objects.all().order_by('-schedule_date')
        all_records = PatientRecord.objects.all()
    elif is_patient:
        current_patient = request.user.patientrecord
        active_bookings = BookingSlot.objects.filter(registered_patient=current_patient).order_by('-schedule_date')
        all_records = [current_patient]
    else:
        active_bookings = []
        all_records = []

    context = {
        'bookings': active_bookings,
        'patients': all_records,
        'specialists': MedicalSpecialist.objects.all(),
        'is_staff': is_staff,
        'is_patient': is_patient,
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

def patient_signup_view(request):
    """Public portal allowing new users to provision encrypted patient records."""
    if request.user.is_authenticated:
        return redirect('dashboard_url')

    if request.method == "POST":
        u_name = request.POST.get('account_user')
        u_pass = request.POST.get('account_pass')
        p_name = request.POST.get('client_name')
        p_age = request.POST.get('client_age')
        p_gender = request.POST.get('client_gender')
        p_phone = request.POST.get('client_phone')

        # Integrity Checks
        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Username already registered in our system.")
            return render(request, 'signup.html')

        if u_name and u_pass and p_name:
            # 1. Base User create karein (Encrypted)
            new_user = User.objects.create_user(username=u_name, password=u_pass)
            
            # 2. Patient Record create karke secure profile linkage lagayein
            PatientRecord.objects.create(
                user_auth=new_user,
                full_name=p_name,
                age_years=p_age,
                gender_identity=p_gender,
                phone_primary=p_phone
            )
            
            # 3. Direct Login session start karein
            login(request, new_user)
            messages.success(request, "Account provisioned successfully!")
            return redirect('dashboard_url')

    return render(request, 'signup.html')


def global_login_view(request):
    """Central gateway routing users to their respective privilege-based context."""
    if request.user.is_authenticated:
        return redirect('dashboard_url')

    if request.method == "POST":
        u_name = request.POST.get('input_user')
        u_pass = request.POST.get('input_pass')
        
        user = authenticate(request, username=u_name, password=u_pass)
        if user is not None:
            login(request, user)
            return redirect('dashboard_url')
        else:
            messages.error(request, "Invalid security credentials.")

    return render(request, 'login.html')


def global_logout_view(request):
    """Flushes active sessions completely."""
    logout(request)
    return redirect('login_url')

@login_required(login_url='login_url')
def create_appointment_slot(request):
    """Processes booking validation and restricts patient visibility based on roles."""
    is_staff = request.user.is_superuser or request.user.is_staff
    is_patient = hasattr(request.user, 'patientrecord')

    if request.method == "POST":
        doc_id = request.POST.get('doc_selection')
        # Agar user staff hai to input form se ID lega, warna logged-in patient ki apni ID inject hogi
        pat_id = request.POST.get('pat_selection') if is_staff else request.user.patientrecord.id
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
            
    # --- GET Request Data Isolation ---
    all_specialists = MedicalSpecialist.objects.all()
    
    if is_staff:
        # Staff can assign slots to any patient in the database
        filtered_patients = PatientRecord.objects.all()
    elif is_patient:
        # Standard patient can only view themselves in the allocation pipeline
        filtered_patients = [request.user.patientrecord]
    else:
        filtered_patients = []

    context = {
        'specialists': all_specialists, 
        'patients': filtered_patients,
        'is_staff': is_staff
    }
    return render(request, 'schedule_slot.html', context)

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