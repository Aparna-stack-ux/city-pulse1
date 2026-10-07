from django.contrib import admin
from .models import USSDUser, USSDSession


@admin.register(USSDUser)
class USSDUserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "created_at")


@admin.register(USSDSession)
class USSDSessionAdmin(admin.ModelAdmin):
    list_display = (
        "phone_number",
        "current_menu",
        "created_at",
    )
