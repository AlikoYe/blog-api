from django.urls import path
from apps.notifications.views import (
    NotificationCountView,
    NotificationListView,
    NotificationReadView,
)

urlpatterns = [
    path("count/", NotificationCountView.as_view(), name="notifications_count"),
    path("list/", NotificationReadView.as_view(), name="notifications_read"),
    path("", NotificationListView.as_view(), name="notifications_list"),
]
