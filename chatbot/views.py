import json

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from .services import ChatbotServiceError, generate_reply


def _is_rate_limited(request):
    address = request.META.get('REMOTE_ADDR', 'unknown')
    key = f'chatbot-rate:{address}'
    if cache.add(key, 1, timeout=60):
        return False
    try:
        return cache.incr(key) > 12
    except ValueError:
        cache.add(key, 1, timeout=60)
        return False


@require_http_methods(['GET', 'POST'])
def chatbot_view(request):
    if request.method == 'POST':
        if _is_rate_limited(request):
            return JsonResponse({'error': _('Too many messages. Please wait a minute and try again.')}, status=429)
        if len(request.body) > 16000:
            return JsonResponse({'error': _('Chat request is too large.')}, status=413)

        try:
            payload = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': _('Send a valid chat message.')}, status=400)

        messages = payload.get('messages') if isinstance(payload, dict) else None
        if not isinstance(messages, list) or not messages:
            return JsonResponse({'error': _('Send a message to continue.')}, status=400)

        clean_messages = []
        for message in messages[-12:]:
            if not isinstance(message, dict) or message.get('role') not in {'user', 'assistant'}:
                continue
            content = message.get('content')
            if not isinstance(content, str) or not content.strip():
                continue
            clean_messages.append({'role': message['role'], 'content': content.strip()[:1000]})

        if not clean_messages or clean_messages[-1]['role'] != 'user':
            return JsonResponse({'error': _('Send a valid user message.')}, status=400)

        try:
            reply = generate_reply(clean_messages)
        except ChatbotServiceError as exc:
            return JsonResponse({'error': str(exc)}, status=exc.status)
        return JsonResponse({'reply': reply})

    return render(request, 'chatbot/chatbot.html', {
        'chatbot_ready': bool(settings.OPENAI_API_KEY),
        'chatbot_messages': {
            'emptyHistory': _('Your recent assistant actions will appear here.'),
            'fileKept': _('File kept on this device; not shared: %(name)s'),
            'selectedPreview': _('Selected attachment preview'),
            'removeAttachment': _('Remove attachment'),
            'assistantPreparing': _('Assistant is preparing guidance'),
            'serviceUnavailable': _('The AI service is temporarily unavailable.'),
            'chooseSmallerFile': _('Choose a file smaller than 10 MB.'),
            'locationUnavailable': _('Location is not available in this browser.'),
            'waitingForLocation': _('Waiting for location permission...'),
            'locationFound': _('Location found: %(latitude)s, %(longitude)s'),
            'locationDenied': _('Location permission was not granted. You can still enter a place in your message.'),
            'locationReportPrompt': _('Help me report an issue near coordinates %(latitude)s, %(longitude)s'),
            'historyCleared': _('Recent actions and this conversation were cleared.'),
            'openReport': _('Open a report'),
            'reportIssue': _('Report an issue'),
            'viewHotspots': _('View hotspots'),
            'startReport': _('Start a report'),
            'openMap': _('Open the map'),
            'reportWaterIssue': _('Report a water issue'),
            'openLiveMap': _('Open live map'),
            'checkCityWeather': _('Check city weather'),
            'viewMyReports': _('View my reports'),
            'createReport': _('Create a report'),
            'emergencyReply': _('If someone is in immediate danger, call your local emergency number now. For a city-service issue, include the exact location and what is happening in a report.'),
            'garbageReply': _('For a waste or cleanliness issue, create a report, choose the closest category, add a clear location, and include a photo if useful.'),
            'roadReply': _('Describe the road or street issue and where it is. A nearby landmark helps the city team locate it quickly.'),
            'waterReply': _('For a water or drainage problem, add the affected street or landmark and say whether the issue is ongoing or intermittent.'),
            'mapReply': _('The live city map shows reported incidents and hotspot locations. You can search by place and explore the available markers.'),
            'weatherReply': _('The weather page shows current conditions and the available forecast for a searched city.'),
            'reportsReply': _('Open your reports to review the current status and details of complaints you have submitted.'),
            'generalReply': _('I can help with a city-service report, road or water issue, waste hotspot, local weather, or tracking a submitted report. What are you trying to do?'),
        },
    })
