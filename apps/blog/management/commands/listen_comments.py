import json
import logging
from django.core.management.base import BaseCommand
from apps.blog.services import COMMENTS_CHANNEL, get_redis_client
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Subscribe to Redis comments channel and print events'
    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.SUCCESS(f'Subscribing to Redis channel: "{COMMENTS_CHANNEL}"'))
        self.stdout.write('Waiting for new comments... (Ctrl+C to stop)\n')
        client = get_redis_client()
        pubsub = client.pubsub()
        pubsub.subscribe(COMMENTS_CHANNEL)

        try:
            for message in pubsub.listen():
                if message['type'] != 'message':
                    continue

                try:
                    data = json.loads(message['data'])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'\n--- New Comment ---\n'
                            f'Post:   {data["post_slug"]}\n'
                            f'Author: {data["author"]}\n'
                            f'Body:   {data["body"]}\n'
                        )
                    )
                    logger.info('Received comment event: post="%s" by %s',data['post_slug'],data['author'],)
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning('Invalid message received: %s - %s', message['data'], e)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nUnsubscribed. Goodbye!'))
        finally:
            pubsub.unsubscribe(COMMENTS_CHANNEL)
            pubsub.close()