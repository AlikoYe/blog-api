import logging
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer

logger = logging.getLogger(__name__)


class NotificationCountView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["notifications"],
        summary="get unread notifications count",
        description="return count of unread notifications for authenticated user",
        responses={
            200: OpenApiResponse(description="Unread notifications count"),
            400: OpenApiResponse(description="Authentification error"),
        },
        examples=[
            OpenApiExample(
                "Count response",
                value={"unread_count": 5},
                response_only=True,
            )
        ],
    )
    def get(self, request: Request) -> Response:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return Response({"unread_count": unread_count})


class NotificationListView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["notifications"],
        summary="notifications list",
        description="return notifications list for authenticated user",
        responses={
            200: NotificationSerializer(many=True),
            400: OpenApiResponse(description="Authentification error"),
        },
    )
    def get(self, request: Request) -> Response:
        notifications = Notification.objects.filter(
            recipient=request.user,
        ).select_related(
            "comment__author",
            "comment__post",
        )
        page = int(request.query_params.get("page", 1))
        page_size = 10
        start = (page - 1) * page_size
        end = start + page_size
        total = notifications.count()
        page_data = notifications[start:end]
        serializer = NotificationSerializer(page_data, many=True)
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": serializer.data,
            }
        )


class NotificationReadView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["notifications"],
        summary="mark all notifications as read",
        description="mark all unread notifications as read for authenticated user",
        responses={
            200: OpenApiResponse(description="Notifications marked as read"),
            401: OpenApiResponse(description="Authentification error"),
        },
        examples=[
            OpenApiExample(
                "Read response",
                value={"marked_read": 5},
                response_only=True,
            ),
        ],
    )
    def post(self, request: Request) -> Response:
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        logger.info(
            "Marked %d notifications as read for %s", updated, request.user.email
        )
        return Response({"marked_read": updated})
