from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from apps.users.throttles import THROTTLE_MESSAGE

def custom_exception_handler(exc: Exception, context: dict) -> Response:
    response = exception_handler(exc, context)
    if isinstance(exc, Throttled):
        response.data = {'detail': THROTTLE_MESSAGE}
    return response