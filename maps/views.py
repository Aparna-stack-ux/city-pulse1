from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from complaints.models import Complaint


INDIA_GARBAGE_HOTSPOTS = [
    {
        'lat': 28.6814,
        'lng': 77.3310,
        'title': 'Ghazipur Landfill',
        'location': 'East Delhi, Delhi',
        'category': _('Garbage hotspot'),
        'status': _('Major landfill'),
        'description': _('One of Delhi\'s largest landfill sites.'),
    },
    {
        'lat': 28.7350,
        'lng': 77.1640,
        'title': 'Bhalswa Landfill',
        'location': 'North Delhi, Delhi',
        'category': _('Garbage hotspot'),
        'status': _('Major landfill'),
        'description': _('Large landfill site with recurring waste fires.'),
    },
    {
        'lat': 28.5300,
        'lng': 77.3000,
        'title': 'Okhla Landfill',
        'location': 'South Delhi, Delhi',
        'category': _('Garbage hotspot'),
        'status': _('Major landfill'),
        'description': _('Long-running landfill and waste processing area.'),
    },
    {
        'lat': 23.0750,
        'lng': 72.5400,
        'title': 'Pirana Landfill',
        'location': 'Ahmedabad, Gujarat',
        'category': _('Garbage hotspot'),
        'status': _('Major landfill'),
        'description': _('Decades-old dumping ground affecting nearby communities.'),
    },
    {
        'lat': 13.1190,
        'lng': 77.5330,
        'title': 'Mavallipura Dumping Zone',
        'location': 'Bengaluru, Karnataka',
        'category': _('Garbage hotspot'),
        'status': _('Waste dumping zone'),
        'description': _('Controversial dumping zone with reported leachate concerns.'),
    },
    {
        'lat': 30.9010,
        'lng': 75.8573,
        'title': 'Ludhiana Waste Hotspot',
        'location': 'Ludhiana, Punjab',
        'category': _('Garbage hotspot'),
        'status': _('Low waste-management performance'),
        'description': _('City identified for waste separation and treatment challenges.'),
    },
    {
        'lat': 13.0827,
        'lng': 80.2707,
        'title': 'Chennai Waste Hotspot',
        'location': 'Chennai, Tamil Nadu',
        'category': _('Garbage hotspot'),
        'status': _('Urban waste pressure'),
        'description': _('Plastic waste and blocked drainage remain major concerns.'),
    },
    {
        'lat': 23.3441,
        'lng': 85.3096,
        'title': 'Ranchi Waste Hotspot',
        'location': 'Ranchi, Jharkhand',
        'category': _('Garbage hotspot'),
        'status': _('Collection gap'),
        'description': _('Inconsistent door-to-door waste collection is reported.'),
    },
    {
        'lat': 12.9716,
        'lng': 77.5946,
        'title': 'Bengaluru Waste Hotspot',
        'location': 'Bengaluru, Karnataka',
        'category': _('Garbage hotspot'),
        'status': _('Urban waste pressure'),
        'description': _('Waste-processing capacity and illegal dumping are concerns.'),
    },
]


def city_map(request):
    complaints = Complaint.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False,
    ).order_by('-created_at')

    map_points = []
    for complaint in complaints:
        category = complaint.get_category_display()
        map_points.append({
            'lat': float(complaint.latitude),
            'lng': float(complaint.longitude),
            'title': complaint.title,
            'location': complaint.location,
            'category': category,
            'status': complaint.get_status_display(),
            'category_code': complaint.category,
            'status_code': complaint.status,
            'priority_code': complaint.priority,
            'is_garbage': complaint.category == 'garbage',
        })

    hotspot_points = [
        {
            **hotspot,
            'is_garbage': True,
            'is_hotspot': True,
            'category_code': 'garbage',
            'status_code': 'hotspot',
            'priority_code': 'low',
        }
        for hotspot in INDIA_GARBAGE_HOTSPOTS
    ]
    all_map_points = map_points + hotspot_points

    context = {
        'map_points': all_map_points,
            'map_points_json': all_map_points,
        'total_complaints': len(map_points),
        'hotspot_count': len(hotspot_points),
        'map_ui': {
            'mapUnavailable': _('The interactive map library could not load in this browser.'),
            'tilesUnavailable': _('Map tiles could not load. Check your internet connection; the location list remains available.'),
            'location': _('Location:'),
            'category': _('Category:'),
            'status': _('Status:'),
            'reportedProblemSingular': _('reported problem'),
            'reportedProblemPlural': _('reported problems'),
            'found': _('found.'),
            'reportedNearSingular': _('reported problem found near %(query)s.'),
            'reportedNearPlural': _('reported problems found near %(query)s.'),
            'noMatches': _('No reported problems matched that search.'),
            'showHotspots': _('Showing garbage hotspots.'),
            'showReports': _('Showing citizen reports.'),
            'showAll': _('Showing all locations.'),
            'searchingPlace': _('Searching for %(query)s...'),
            'placeNotFound': _('No place found for %(query)s.'),
            'showingPlace': _('Showing %(place)s. Existing complaint markers remain visible nearby.'),
            'searchUnavailable': _('Place search is temporarily unavailable. Try a complaint title or location.'),
            'noComplaintAtPlace': _('No complaint is recorded at this exact place yet.'),
        },
    }
    return render(request, 'maps/map.html', context)
