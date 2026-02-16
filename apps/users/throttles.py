from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

REGISTER_RATE = '5/minute'
LOGIN_RATE = '10/minute'
POST_CREATION_RATE = '20/minute'
THROTTLE_MESSAGE = 'Too many requests, try again later'

class RegisterThrottle(AnonRateThrottle):
    rate = REGISTER_RATE
    scope = 'register'

class LoginThrottle(AnonRateThrottle):
    rate = LOGIN_RATE
    scope = 'login'

class PostCreationThrottle(UserRateThrottle):
    rate = POST_CREATION_RATE
    scope = 'post_creation'