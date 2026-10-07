from django.contrib import admin
from .models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'priority', 'status', 'created_at')
    list_filter = ('category', 'priority', 'status', 'created_at')
    search_fields = ('title', 'description', 'location', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
