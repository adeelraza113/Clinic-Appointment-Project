from django.db import models

class MedicalSpecialist(models.Model):
    expert_name = models.CharField(max_length=150)
    field_of_expertise = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Dr. {self.expert_name} ({self.field_of_expertise})"


class PatientRecord(models.Model):
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