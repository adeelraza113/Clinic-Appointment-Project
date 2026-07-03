from django.contrib.auth.models import User
from django.db import models

class MedicalSpecialist(models.Model):
    user_auth = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    expert_name = models.CharField(max_length=150)
    field_of_expertise = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Dr. {self.expert_name}"


class PatientRecord(models.Model):
    user_auth = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    age_years = models.IntegerField()
    gender_identity = models.CharField(max_length=15, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    phone_primary = models.CharField(max_length=20)
    health_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.full_name


class BookingSlot(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    assigned_doctor = models.ForeignKey(MedicalSpecialist, on_delete=models.CASCADE)
    registered_patient = models.ForeignKey(PatientRecord, on_delete=models.CASCADE)
    schedule_date = models.DateField()
    schedule_time = models.TimeField()
    current_status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Active')
    creation_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registered_patient.full_name} -> {self.assigned_doctor.expert_name} on {self.schedule_date}"
    
class ClinicalPrescription(models.Model):
    """Stores high-confidentiality check-up summary and drugs prescribed by the specialist."""
    associated_booking = models.OneToOneField('BookingSlot', on_delete=models.CASCADE, related_name='medical_record')
    symptoms_observed = models.TextField()
    prescribed_medication = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record for Booking #{self.associated_booking.id}"


class FinancialInvoice(models.Model):
    """Automated billing accounting engine calculating base fees, clinical taxes, and grand totals."""
    linked_booking = models.OneToOneField('BookingSlot', on_delete=models.CASCADE, related_name='invoice')
    base_consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)
    healthcare_tax = models.DecimalField(max_digits=6, decimal_places=2, default=150.00) # Fixed hospital service tax
    grand_total_payable = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=15, default='Unpaid', choices=[('Unpaid', 'Unpaid'), ('Settled', 'Settled')])
    generated_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"INV-{self.id} | Total: {self.grand_total_payable}"