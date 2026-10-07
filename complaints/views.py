from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ComplaintForm
from .models import Complaint


@login_required
def complaint_list(request):
    complaint_pages = Paginator(
        Complaint.objects.filter(user=request.user).order_by("-created_at"),
        10,
    )
    complaints = complaint_pages.get_page(request.GET.get("page"))
    return render(
        request,
        "complaints/complaint_list.html",
        {"complaints": complaints},
    )


@login_required
def complaint_create(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.user = request.user
            complaint.source = "WEB"
            complaint.save()
            return redirect("complaint_detail", pk=complaint.pk)
    else:
        form = ComplaintForm()

    recent_complaints = Complaint.objects.filter(user=request.user).order_by(
        "-created_at"
    )[:5]
    return render(
        request,
        "complaints/complaint_form.html",
        {"form": form, "recent_complaints": recent_complaints},
    )


@login_required
def complaint_detail(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, user=request.user)
    return render(
        request,
        "complaints/complaint_detail.html",
        {"complaint": complaint},
    )


@login_required
def complaint_status(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk, user=request.user)
    return render(
        request,
        "complaints/complaint_status.html",
        {"complaint": complaint},
    )