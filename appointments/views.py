from django.shortcuts import get_object_or_404, render, redirect
from django.db import transaction
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from django.db.models import Sum, Count, Q
from django.utils import timezone
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

    is_staff = request.user.is_superuser or request.user.is_staff
    is_doctor = hasattr(request.user, 'medicalspecialist')
    is_patient = hasattr(request.user, 'patientrecord')
    grand_footprint = Decimal("0.00")
    queue_load = 0
    doctors_load = []
    medical_history = []
    active_bookings = BookingSlot.objects.none()
    if is_staff:

        active_bookings = (
            BookingSlot.objects
            .select_related(
                'registered_patient',
                'assigned_doctor'
            )
            .order_by('-schedule_date', '-schedule_time')
        )

        completed_slots = BookingSlot.objects.filter(
            current_status="Completed"
        )
        total_revenue = completed_slots.aggregate(
            revenue=Sum("assigned_doctor__consultation_fee")
        )["revenue"] or Decimal("0.00")

        hospital_markup = (
            Decimal(completed_slots.count()) *
            Decimal("250.00")
        )
        grand_footprint = total_revenue + hospital_markup
        today = timezone.now().date()
        queue_load = BookingSlot.objects.filter(
            current_status="Pending",
            schedule_date=today
        ).count()

        doctors_load = (
            MedicalSpecialist.objects
            .annotate(
                completed_cases=Count(
                    "bookingslot",
                    filter=Q(
                        bookingslot__current_status="Completed"
                    )
                )
            )
            .order_by("-completed_cases")
        )
    elif is_doctor:
        current_doctor = request.user.medicalspecialist

        active_bookings = (
            BookingSlot.objects
            .filter(
                assigned_doctor=current_doctor
            )
           .select_related(
         'registered_patient',
         'assigned_doctor',
         'medical_record',
        'invoice'
     )
            .order_by('-schedule_date', '-schedule_time')
        )
    elif is_patient:
        current_patient = request.user.patientrecord
        active_bookings = (
            BookingSlot.objects
            .filter(
                registered_patient=current_patient
            )
            .select_related(
                'assigned_doctor'
            )
            .order_by('-schedule_date', '-schedule_time')
        )

        medical_history = (
    BookingSlot.objects
    .filter(
        registered_patient=current_patient,
        current_status='Completed'
    )
    .select_related(
        'assigned_doctor',
        'medical_record',
        'invoice'
    )
    .order_by('-schedule_date', '-schedule_time')
)

    else:
        active_bookings = BookingSlot.objects.none()

    context = {
        'bookings': active_bookings,
        'is_staff': is_staff,
        'is_doctor': is_doctor,
        'is_patient': is_patient,
        'grand_footprint': grand_footprint,
        'queue_load': queue_load,
        'doctors_load': doctors_load,
        'medical_history': medical_history,
    }
    return render(
        request,
        'dashboard.html',
        context
    )

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
        base_fee = Decimal(str(booking.assigned_doctor.consultation_fee))
        tax_percentage = Decimal('0.05') 
        tax = base_fee * tax_percentage
        grand_total = base_fee + tax
        
        FinancialInvoice.objects.create(linked_booking=booking, base_consultation_fee=base_fee, healthcare_tax=tax, grand_total_payable=grand_total)
        booking.current_status = 'Completed'
        booking.save()
        
        messages.success(request, "Prescription saved and invoice generated successfully!")
        return redirect('dashboard_url')
        
    return render(request, 'add_prescription.html', {'booking': booking})


@login_required(login_url='login_url')
def view_invoice_view(request, slot_id):
    """
    Secure invoice view for Patients, Doctors and Staff.
    """
    booking = get_object_or_404(
        BookingSlot.objects.select_related(
            "assigned_doctor",
            "registered_patient",
            "invoice"
        ),
        id=slot_id
    )
    is_staff = request.user.is_staff or request.user.is_superuser
    is_doctor = (
        hasattr(request.user, "medicalspecialist") and
        booking.assigned_doctor == request.user.medicalspecialist
    )
    is_patient = (
        hasattr(request.user, "patientrecord") and
        booking.registered_patient == request.user.patientrecord
    )
    if not (is_staff or is_doctor or is_patient):
        messages.error(
            request,
            "Access Violation: Unauthorized Invoice Request."
        )
        return redirect("dashboard_url")

    invoice = get_object_or_404(
        FinancialInvoice,
        linked_booking=booking
    )
    context = {
        "booking": booking,
        "doctor": booking.assigned_doctor,
        "patient": booking.registered_patient,
        "invoice": invoice,
        "consultation_fee": invoice.base_consultation_fee,
        "hospital_charges": invoice.healthcare_tax,
        "grand_total": invoice.grand_total_payable,
        "payment_status": invoice.payment_status,
        "generated_date": invoice.generated_date,
    }

    return render(
        request,
        "invoice_detail.html",
        context
    )


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
    """Secure administrative view to onboard doctors matching strict DB schema guidelines."""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access Denied: Administrative privileges required.")
        return redirect('dashboard_url')

    if request.method == "POST":
        u_name = request.POST.get('doc_user')
        u_pass = request.POST.get('doc_pass')
        d_name = request.POST.get('expert_name')
        d_spec = request.POST.get('specialization')
        d_phone = request.POST.get('contact_number') 
        d_fee = request.POST.get('consultation_fee')


        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Error: This username is already registered.")
            return render(request, 'onboard_doctor.html')

        try:
            with transaction.atomic():
                new_doc_user = User.objects.create_user(username=u_name, password=u_pass)
                
                MedicalSpecialist.objects.create(
                    user_auth=new_doc_user,
                    expert_name=d_name,
                    field_of_expertise=d_spec, 
                    contact_number=d_phone,      
                    consultation_fee=d_fee      
                )
                
            messages.success(request, f"Dr. {d_name} has been successfully onboarded into the ecosystem.")
            return redirect('dashboard_url')
            
        except Exception as e:
            messages.error(request, f"Database Integrity Failure: {str(e)}")
            
    return render(request, 'onboard_doctor.html')



@login_required(login_url='login_url')
def treat_patient_view(request, slot_id):
    """Secured clinical view to transition appointment states and record observations."""
    booking = get_object_or_404(BookingSlot, id=slot_id)
    
    is_assigned_doctor = hasattr(request.user, 'medicalspecialist') and booking.assigned_doctor == request.user.medicalspecialist
    
    if not is_assigned_doctor:
        messages.error(request, "Access Denied: You are not the assigned specialist for this patient transaction.")
        return redirect('dashboard_url')
        
    if booking.current_status == 'Completed':  
        messages.warning(request, "Clinical log warning: This case entry is already locked and completed.")
        return redirect('dashboard_url')

    if request.method == "POST":
        clinical_notes = request.POST.get('clinical_notes')
        medication_plan = request.POST.get('medication_plan')
        
        try:
            with transaction.atomic():
                booking.current_status = 'Completed'
                
                if hasattr(booking, 'doctor_notes'):
                    booking.doctor_notes = clinical_notes
                if hasattr(booking, 'prescription_details'):
                    booking.prescription_details = medication_plan
                    
                booking.save()
                
            messages.success(request, f"Medical chart updated successfully for Patient: {booking.registered_patient.patient_name}.")
            return redirect('dashboard_url')
            
        except Exception as e:
            messages.error(request, f"Pipeline Error committing clinical transaction: {str(e)}")

    context = {
        'booking': booking,
        'patient': booking.registered_patient
    }
    return render(request, 'treat_patient.html', context)

