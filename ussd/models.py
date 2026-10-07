from django.db import models
from complaints.models import Complaint


class USSDUser(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_number


class USSDSession(models.Model):
    phone_number = models.CharField(max_length=15)
    current_menu = models.CharField(
        max_length=50,
        default="main"
    )
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for {self.phone_number} at {self.created_at}"