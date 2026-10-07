from django.conf import settings
from django.utils.translation import get_language


NATIVE_LANGUAGE_NAMES = {
    'en': 'English',
    'hi': 'हिन्दी',
    'ml': 'മലയാളം',
    'ta': 'தமிழ்',
    'te': 'తెలుగు',
    'kn': 'ಕನ್ನಡ',
    'bn': 'বাংলা',
    'mr': 'मराठी',
    'gu': 'ગુજરાતી',
    'pa': 'ਪੰਜਾਬੀ',
    'or': 'ଓଡ଼ିଆ',
    'as': 'অসমীয়া',
    'ur': 'اردو',
}


def language_context(request):
    configured_languages = [language_code for language_code, _ in settings.LANGUAGES]
    return {
        'current_language': get_language(),
        'native_languages': [
            (language_code, NATIVE_LANGUAGE_NAMES[language_code])
            for language_code in configured_languages
        ],
    }