from django.urls import path
from . import views

urlpatterns = [
    path("", views.simulator, name="ussd_simulator"),
]