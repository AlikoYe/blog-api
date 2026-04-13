import asyncio
import logging
from django.http import StreamingHttpResponse
from redis import asyncio as aioredis
from settings.conf import BLOG_REDIS_URL

logger = logging.getLogger(__name__)

SSE_CHANNEL = "post_published"
SSE_HEARTBEAT_SECONDS = 15


async def post_stream_view(request):
    response = StreamingHttpResponse(
        _event_generator(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Redirect"] = "no"
    return response


async def _event_generator():
    client = aioredis.from_url(BLOG_REDIS_URL)
    pubsub = client.pubsub()
    await pubsub.subscribe(SSE_CHANNEL)

    logger.info("SSE client connected to post publication stream")

    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    _get_next_message(pubsub),
                    timeout=SSE_HEARTBEAT_SECONDS,
                )
                if message and message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    yield f"data: {data}\n\n"
                    logger.debug("SSE event sent: %s", data)

            except asyncio.TimeoutError:
                yield ":heartbeat\n\n"

    except asyncio.CancelledError:
        logger.info("SSE client disconnected")
    except Exception:
        logger.exception("SSE stream error")
    finally:
        await pubsub.unsubscribe(SSE_CHANNEL)
        await pubsub.aclose()
        await client.aclose()


async def _get_next_message(pubsub):
    while True:
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if message:
            return message
        await asyncio.sleep(1.0)
