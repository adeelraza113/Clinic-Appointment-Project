from django.contrib import admin
from django.urls import path, include

admin.site.site_header = "Sird Administration Engine"
admin.site.site_title = "Sird Admin Portal"
admin.site.index_title = "Control Panel"
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('appointments.urls')), 
]
