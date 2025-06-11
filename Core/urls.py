from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('Home.urls')),  # routes all Home app APIs under /api/
]
