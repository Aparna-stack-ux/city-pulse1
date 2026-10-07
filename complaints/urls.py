from django.urls import path
from .views import complaint_list, complaint_create, complaint_detail, complaint_status

urlpatterns = [
    path('', complaint_list, name='complaint_list'),
    path('new/', complaint_create, name='complaint_create'),
    path('<int:pk>/', complaint_detail, name='complaint_detail'),
    path('<int:pk>/status/', complaint_status, name='complaint_status'),
]
