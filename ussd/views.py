from django.shortcuts import render
from django.utils.translation import gettext as _

# Create your viewsfrom django.shortcuts import render
from .models import USSDUser, USSDSession


def simulator(request):

    if request.method == "GET":

        message = _("""Welcome to CityPulse

    Enter your mobile number to continue:""")

        request.session["ussd_state"] = "phone"

        return render(
            request,
            "ussd/simulator.html",
            {"message": message}
        )

    user_input = request.POST.get("user_input", "").strip()

    state = request.session.get(
        "ussd_state",
        "phone"
    )

    # STEP 1 - Mobile number
    if state == "phone":

        phone = user_input

        USSDUser.objects.get_or_create(
            phone_number=phone
        )

        request.session["phone_number"] = phone
        request.session["ussd_state"] = "main"

        message = _("""Welcome to CityPulse

1. Report Complaint
2. Track Complaint
3. Emergency
4. Weather
5. My Complaints

Enter your choice:""")

        return render(
            request,
            "ussd/simulator.html",
            {"message": message}
        )

    # STEP 2 - Main menu
    if state == "main":

        if user_input == "1":

            request.session["ussd_state"] = "complaint_category"

            message = _("""REPORT COMPLAINT

1. Road
2. Water
3. Garbage
4. Street Light
5. Drainage
6. Other

Enter category:""")

        elif user_input == "2":

            request.session["ussd_state"] = "track"

            message = _("""TRACK COMPLAINT

Enter your Complaint ID:""")

        elif user_input == "3":

            message = _("""EMERGENCY

Please contact the appropriate
official emergency service directly.

1. Police
2. Ambulance
3. Fire

Enter 0 to return.""")

        elif user_input == "4":

            message = _("""WEATHER

Weather information will be
connected to the CityPulse
weather service.

Enter 0 to return.""")

        elif user_input == "5":

            message = _("""MY COMPLAINTS

Your complaints will appear here.

Enter 0 to return.""")

        elif user_input == "0":

            message = _("""Welcome to CityPulse

    1. Report Complaint
    2. Track Complaint
    3. Emergency
    4. Weather
    5. My Complaints

    Enter your choice:""")

        else:

            message = _("""Invalid option.

1. Report Complaint
2. Track Complaint
3. Emergency
4. Weather
5. My Complaints""")

        return render(
            request,
            "ussd/simulator.html",
            {"message": message}
        )

    if state == "complaint_category":
        categories = {
            "1": _("Road"),
            "2": _("Water"),
            "3": _("Garbage"),
            "4": _("Street Light"),
            "5": _("Drainage"),
            "6": _("Other"),
        }
        category = categories.get(user_input)
        if category:
            request.session["ussd_category"] = category
            request.session["ussd_state"] = "complaint_location"
            message = _("Enter the location of the problem:")
        else:
            message = _("""Invalid category.

1. Road
2. Water
3. Garbage
4. Street Light
5. Drainage
6. Other

Enter category:""")
        return render(request, "ussd/simulator.html", {"message": message})

    if state == "complaint_location":
        if not user_input:
            message = _("Please enter the location of the problem:")
        else:
            request.session["ussd_location"] = user_input
            request.session["ussd_state"] = "complaint_description"
            message = _("Describe the problem:")
        return render(request, "ussd/simulator.html", {"message": message})

    if state == "complaint_description":
        if not user_input:
            message = _("Please describe the problem:")
            return render(request, "ussd/simulator.html", {"message": message})

        phone = request.session.get("phone_number")
        if not phone:
            request.session["ussd_state"] = "phone"
            message = _("Session expired. Enter your mobile number to restart:")
            return render(request, "ussd/simulator.html", {"message": message})

        report = USSDSession.objects.create(
            phone_number=phone,
            current_menu="completed",
            data={
                "category": request.session.get("ussd_category", "Other"),
                "location": request.session.get("ussd_location", ""),
                "description": user_input,
                "status": "received",
            },
        )
        request.session["ussd_state"] = "main"
        request.session.pop("ussd_category", None)
        request.session.pop("ussd_location", None)
        message = (
            _("Complaint received. Reference: %(reference)s. Enter 0 to return to the menu.")
            % {"reference": f"CP-{report.pk:04d}"}
        )
        return render(request, "ussd/simulator.html", {"message": message})

    if state == "track":
        reference = user_input.upper().removeprefix("CP-").lstrip("#")
        try:
            report_id = int(reference)
        except ValueError:
            report_id = None

        report = None
        phone = request.session.get("phone_number")
        if report_id is not None and phone:
            report = USSDSession.objects.filter(
                pk=report_id,
                phone_number=phone,
                current_menu="completed",
            ).first()

        if report:
            status = report.data.get("status", "received")
            status_label = _("Received") if status == "received" else status
            message = _("Complaint %(reference)s\nStatus: %(status)s\nCategory: %(category)s\nLocation: %(location)s") % {
                "reference": user_input,
                "status": status_label,
                "category": report.data.get("category", _("Unknown")),
                "location": report.data.get("location", _("Unknown")),
            }
        else:
            message = _("Complaint not found for this mobile number. Check the reference and try again.")
        request.session["ussd_state"] = "main"
        return render(request, "ussd/simulator.html", {"message": message})

    request.session.pop("phone_number", None)
    request.session.pop("ussd_category", None)
    request.session.pop("ussd_location", None)
    request.session["ussd_state"] = "phone"
    return render(
        request,
        "ussd/simulator.html",
        {
            "message": _("Session expired. Enter your mobile number to restart:")
        }
    ) 
