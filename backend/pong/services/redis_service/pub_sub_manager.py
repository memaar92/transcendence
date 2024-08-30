from .constants import RedisKeys, MatchSessionFields, REDIS_INSTANCE
from typing import Any, Callable, Optional
from asgiref.sync import sync_to_async
import asyncio
from concurrent.futures import ThreadPoolExecutor


class PubSubManager:
    
    @staticmethod
    async def publish_to_channel(channel: str, message: str) -> None:
        '''Publish a message to a Redis channel'''
        try:
            await sync_to_async(REDIS_INSTANCE.publish)(channel, message)
        except Exception as e:
            print(f"Error publishing to channel: {e}")
    
    @staticmethod
    async def subscribe_to_channel(
        pubsub: Any, 
        channel: str, 
        external_handler: Optional[Callable[[Any], None]] = None
    ) -> None:
        '''Subscribe to a Redis channel and handle messages with an external handler'''
        try:
            await sync_to_async(pubsub.subscribe)(channel)
            print(f"Subscribed to channel: {channel}")

            # Run the listener in a separate thread
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                await loop.run_in_executor(pool, PubSubManager._listen_to_channel, pubsub, external_handler)
        except Exception as e:
            print(f"Error subscribing to channel: {e}")

    @staticmethod
    def _listen_to_channel(pubsub: Any, external_handler: Optional[Callable[[Any], None]]) -> None:
        '''Blocking listener for Redis channel to be run in a separate thread'''
        handler = external_handler if external_handler else PubSubManager.message_handler
        for message in pubsub.listen():
            # Running the handler in the event loop
            asyncio.run(handler(message))

    @staticmethod
    async def unsubscribe_from_channel(pubsub: Any, channel: str) -> None:
        '''Unsubscribe from a Redis channel'''
        try:
            await sync_to_async(pubsub.unsubscribe)(channel)
            print(f"Unsubscribed from channel: {channel}")
        except Exception as e:
            print(f"Error unsubscribing from channel: {e}")

    @staticmethod
    async def publish_match_state_channel(match_id: str, state: str) -> None:
        '''Publish the match state to the Redis channel'''
        channel = f"{RedisKeys.MATCHES_OPEN}:{match_id}:{MatchSessionFields.STATE}"
        await PubSubManager.publish_to_channel(channel, state)

    @staticmethod
    async def subscribe_to_match_state_channel(pubsub: Any, match_id: str, external_handler: Optional[Callable[[Any], None]] = None) -> None:
        '''Subscribe to the match state channel'''
        channel = f"{RedisKeys.MATCHES_OPEN}:{match_id}:{MatchSessionFields.STATE}"
        await PubSubManager.subscribe_to_channel(pubsub, channel, external_handler)

    @staticmethod
    async def unsubscribe_from_match_state_channel(pubsub: Any, match_id: str) -> None:
        '''Unsubscribe from the match state channel'''
        channel = f"{RedisKeys.MATCHES_OPEN}:{match_id}:{MatchSessionFields.STATE}"
        await PubSubManager.unsubscribe_from_channel(pubsub, channel)

    @staticmethod
    async def message_handler(message: Any) -> None:
        '''Default message handler'''
        if message['type'] == 'message':
            data = message['data']
            if isinstance(data, bytes):
                # If data is bytes, decode it to a string
                data = data.decode('utf-8')
            elif isinstance(data, int):
                # If data is an integer, handle it as needed (e.g., convert to string or log it)
                data = str(data)
            print(f"Received message: {data}")

