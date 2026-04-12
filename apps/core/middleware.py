import logging
import zoneinfo

from django.conf import settings
from django.utils import timezone, translation

logger = logging.getLogger(__name__)

LANG_QUERY_PARAM = "lang"
SUPPORTED_LANGUAGES = {code for code, _ in settings.LANGUAGES}


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = self._resolve_language(request)
        translation.activate(language)
        request.LANGUAGE_CODE = language

        self._activate_timezone(request)

        response = self.get_response(request)
        translation.deactivate()
        return response

    def _resolve_language(self, request) -> str:
        if hasattr(request, "user") and request.user.is_authenticated:
            user_lang = getattr(request.user, "language", None)
            if user_lang and user_lang in SUPPORTED_LANGUAGES:
                logger.debug("Language from user profile: %s", user_lang)
                return user_lang

        query_lang = request.GET.get(LANG_QUERY_PARAM)
        if query_lang and query_lang in SUPPORTED_LANGUAGES:
            logger.debug("Language from query param: %s", query_lang)
            return query_lang

        accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
        for lang_code in self._parse_accept_language(accept_lang):
            if lang_code in SUPPORTED_LANGUAGES:
                logger.debug("Language from Accept-Language header: %s", lang_code)
                return lang_code

        logger.debug("Using default language: %s", settings.LANGUAGE_CODE)
        return settings.LANGUAGE_CODE

    def _parse_accept_language(self, header: str) -> list:
        if not header:
            return []

        languages = []
        for part in header.split(","):
            part = part.strip()
            if ";" in part:
                lang, quality = part.split(";", 1)
                try:
                    q = float(quality.split("=")[1])
                except (IndexError, ValueError):
                    q = 1.0
            else:
                lang = part
                q = 1.0

            lang_code = lang.strip().split("-")[0].lower()
            languages.append((lang_code, q))

        languages.sort(key=lambda x: x[1], reverse=True)
        return [lang for lang, _ in languages]

    def _activate_timezone(self, request) -> None:
        if hasattr(request, "user") and request.user.is_authenticated:
            user_tz = getattr(request.user, "timezone", None)
            if user_tz:
                try:
                    tz = zoneinfo.ZoneInfo(user_tz)
                    timezone.activate(tz)
                    logger.debug("Timezone activated: %s", user_tz)
                    return
                except (KeyError, zoneinfo.ZoneInfoNotFoundError):
                    logger.warning(
                        "Invalid timezone for user %s: %s", request.user.email, user_tz
                    )

        timezone.deactivate()
