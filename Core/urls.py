from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin92!/', admin.site.urls),
    path('api/', include('Home.urls')),  
]
