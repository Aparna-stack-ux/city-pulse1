from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from complaints.models import Complaint
from django.contrib.auth import get_user_model
from weather.services import fetch_weather_summary


def home(request):
    complaint_count = Complaint.objects.count()
    resolved_count = Complaint.objects.filter(status='resolved').count()
    emergency_count = Complaint.objects.filter(
        category='emergency',
        status__in=['pending', 'assigned', 'in_progress'],
    ).count()
    citizen_count = get_user_model().objects.count()
    return render(request, 'home.html', {
        'complaint_count': complaint_count,
        'resolved_count': resolved_count,
        'emergency_count': emergency_count,
        'citizen_count': citizen_count,
    })


@login_required
def dashboard(request):
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')[:5]
    total = Complaint.objects.filter(user=request.user).count()
    resolved = Complaint.objects.filter(user=request.user, status='resolved').count()
    pending = Complaint.objects.filter(user=request.user, status='pending').count()

    try:
        weather_summary = fetch_weather_summary('London')
    except Exception:
        weather_summary = {
            'city': 'London',
            'temperature': None,
            'description': 'Unable to load weather.',
            'humidity': None,
            'wind_speed': None,
        }

    return render(request, 'dashboard/dashboard.html', {
        'complaints': complaints,
        'total': total,
        'resolved': resolved,
        'pending': pending,
        'weather_summary': weather_summary,
    })
