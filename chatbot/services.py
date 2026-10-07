import requests
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import get_language

CHAT_COMPLETIONS_URL = 'https://api.openai.com/v1/chat/completions'
SYSTEM_PROMPT = (
    'You are the CityPulse civic services assistant. Give concise, practical guidance about '
    'reporting city issues, using CityPulse maps, weather, and tracking complaints. Do not '
    'claim to have submitted a report or accessed private user data. For immediate danger, '
    'tell the user to contact local emergency services. Do not invent emergency phone numbers, '
    'city policies, or live incident information. Ask for a general location only when needed, '
    'and discourage sharing passwords, payment data, or other sensitive personal information.'
)


class ChatbotServiceError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def generate_reply(messages):
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ChatbotServiceError(_('AI assistant is not configured.'), status=503)

    try:
        response = requests.post(
            CHAT_COMPLETIONS_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': settings.OPENAI_MODEL,
                'messages': [
                    {
                        'role': 'system',
                        'content': f'{SYSTEM_PROMPT} Reply in the same language as the user. The selected page language is {get_language()}; use it when the user has not clearly chosen another language.',
                    },
                    *messages,
                ],
                'temperature': 0.4,
                'max_tokens': 500,
            },
            timeout=30,
        )
    except requests.RequestException as exc:
        raise ChatbotServiceError(_('AI service is temporarily unavailable.'), status=502) from exc

    if response.status_code == 401:
        raise ChatbotServiceError(_('The configured OpenAI key was rejected.'), status=503)
    if response.status_code == 429:
        raise ChatbotServiceError(_('The AI service is busy. Please try again shortly.'), status=503)
    if not response.ok:
        raise ChatbotServiceError(_('AI service could not complete the request.'), status=502)

    try:
        reply = response.json()['choices'][0]['message']['content'].strip()
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ChatbotServiceError(_('AI service returned an unreadable response.'), status=502) from exc

    if not reply:
        raise ChatbotServiceError(_('AI service returned an empty response.'), status=502)
    return reply
