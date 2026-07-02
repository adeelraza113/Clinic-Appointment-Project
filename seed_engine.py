import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_project.settings')
django.setup()

from appointments.models import MedicalSpecialist

def deploy_mock_specialists():
    mock_data = [
        {"name": "Faisal Khan", "expert": "Cardiology", "phone": "+923001112223", "fee": 2500.00},
        {"name": "Ayesha Bilal", "expert": "Pediatrics", "phone": "+923214445556", "fee": 2000.00},
        {"name": "Zane Raza", "expert": "Neurology", "phone": "+923337778889", "fee": 3500.00},
    ]
    
    print("Initiating clinic data injection...")
    for item in mock_data:
        obj, created = MedicalSpecialist.objects.get_or_create(
            expert_name=item["name"],
            defaults={
                "field_of_expertise": item["expert"],
                "contact_number": item["phone"],
                "consultation_fee": item["fee"]
            }
        )
        if created:
            print(f"Successfully added: Dr. {item['name']}")
        else:
            print(f"Record already exists: Dr. {item['name']}")
            
    print("Injection process concluded successfully.")

if __name__ == '__main__':
    deploy_mock_specialists()