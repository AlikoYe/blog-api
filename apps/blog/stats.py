import asyncio
import logging

import httpx

from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from apps.blog.models import Comment, Post
from apps.users.models import User

logger = logging.getLogger(__name__)


EXCHANGE_RATES_URL = "https://open.er-api.com/v6/latest/USD"
TIME_API_URL = "https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty"
EXTRACTED_CURRENCIES = ("KZT", "RUB", "EUR")
HTTP_TIMEOUT = 10


async def _fetch_exchange_rates() -> dict:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(EXCHANGE_RATES_URL)
            response.raise_for_status()
            data = response.json()

            rates = data.get("rates", {})
            extracted = {
                currency: rates.get(currency)
                for currency in EXTRACTED_CURRENCIES
                if currency in rates
            }

            logger.info("Exchange rates fetched: %s", extracted)
            return extracted
    except httpx.HTTPError:
        logger.exception("Failed to fetch exchange rates")
        return {}
    except Exception:
        logger.exception("Unexpected error fetching exchange rates")
        return {}


async def _fetch_current_time() -> str:
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(TIME_API_URL)
            response.raise_for_status()
            data = response.json()

            current_time = data.get("dateTime", "")
            logger.info("Current Almaty time fetched: %s", current_time)
            return current_time
    except httpx.HTTPError:
        logger.exception("Failed to fetch current time")
        return ""
    except Exception:
        logger.exception("Unexpected error fetching current time")
        return ""


async def _fetch_external_data() -> tuple:
    exchange_rates, current_time = await asyncio.gather(
        _fetch_exchange_rates(),
        _fetch_current_time(),
    )
    return exchange_rates, current_time


class StatsView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["Stats"],
        summary="Get blog statistics and external data",
        description=(
            "Returns blog statistics (post, comment, user counts) combined with "
            "exchange rates (KZT, RUB, EUR vs USD) and current Almaty time. "
            "External API calls are made concurrently using asyncio.gather. "
            "No authentication required."
        ),
        responses={
            200: OpenApiResponse(
                description="Blog stats with external data.",
            ),
        },
        examples=[
            OpenApiExample(
                "Stats response",
                value={
                    "blog": {
                        "total_posts": 42,
                        "total_comments": 137,
                        "total_users": 15,
                    },
                    "exchange_rates": {
                        "KZT": 450.23,
                        "RUB": 89.10,
                        "EUR": 0.92,
                    },
                    "current_time": "2024-03-15T18:30:00+05:00",
                },
                response_only=True,
            ),
        ],
    )
    def get(self, request: Request) -> Response:
        blog_counts = {
            "total_posts": Post.objects.count(),
            "total_comments": Comment.objects.count(),
            "total_users": User.objects.count(),
        }

        try:
            exchange_rates, current_time = asyncio.run(_fetch_external_data())
        except Exception:
            logger.exception("Failed to fetch external data")
            exchange_rates = {}
            current_time = ""

        return Response(
            {
                "blog": blog_counts,
                "exchange_rates": exchange_rates,
                "current_time": current_time,
            }
        )
