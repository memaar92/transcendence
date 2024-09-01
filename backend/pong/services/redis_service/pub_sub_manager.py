from .constants import RedisKeys, MatchSessionFields, REDIS_INSTANCE
from .key_creation import KeyCreation
from typing import Any, Callable, Optional, Dict, List, Tuple
import asyncio
import logging

logger = logging.getLogger("PongConsumer")

class PubSubManager:
    '''Class to manage Redis Pub/Sub operations'''

    _tasks: Dict[str, List[Tuple[Callable[[Any], None], asyncio.Task]]] = {}

    @staticmethod
    async def publish_to_channel(channel: str, message: str) -> None:
        '''Publish a message to a Redis channel'''
        try:
            await REDIS_INSTANCE.publish(channel, message)
        except Exception as e:
            logger.error(f"Error publishing to channel: {e}")

    @staticmethod
    async def subscribe_to_channel(redis_instance, channel: str, callback: Callable[[Any], None]) -> None:
        logger.info(f"Subscribe to channel triggered")
        pubsub = redis_instance.pubsub()
        await pubsub.subscribe(channel)
    
        async def message_listener():
            logger.info(f"Subscribed to channel: {channel}")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    logger.info(f"Received message: {message}")
                    await callback(message)
                await asyncio.sleep(0.01)  # Sleep briefly to avoid busy-waiting
    
        if channel not in PubSubManager._tasks:
            task = asyncio.create_task(message_listener())
            PubSubManager._tasks[channel] = [(callback, task)]
        else:
            logger.info(f"Channel {channel} already has a task, skipping creation of a new one.")

    @staticmethod
    async def unsubscribe_from_channel(redis_instance, channel: str, callback: Callable[[Any], None]) -> None:
        '''Unsubscribe a specific callback from a Redis channel'''
        pubsub = redis_instance.pubsub()
        logger.info(f"Unsubscribing from channel: {channel}")
        try:
            if channel in PubSubManager._tasks:
                tasks = PubSubManager._tasks[channel]
                for cb, task in tasks:
                    if cb == callback:
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            logger.info(f"Task for channel {channel} with callback {callback} cancelled")
                        tasks.remove((cb, task))
                        break
                if not tasks:
                    await pubsub.unsubscribe(channel)
                    logger.info(f"Unsubscribed from channel: {channel}")
                    del PubSubManager._tasks[channel]
        except Exception as e:
            logger.error(f"Error unsubscribing from channel: {e}")

    @staticmethod
    async def publish_match_state_channel(match_id: str, state: str) -> None:
        '''Publish the match state to the Redis channel'''
        channel = KeyCreation.create_match_session_key(match_id, MatchSessionFields.STATE)
        await PubSubManager.publish_to_channel(channel, state)

    @staticmethod
    async def subscribe_to_match_state_channel(redis_instance: Any, match_id: str, external_handler: Optional[Callable[[Any], None]] = None) -> None:
        '''Subscribe to the match state channel'''
        logger.info(f"Subscribing to match state channel for match {match_id}")
        channel = KeyCreation.create_match_session_key(match_id, MatchSessionFields.STATE)
        await PubSubManager.subscribe_to_channel(redis_instance, channel, external_handler)

    @staticmethod
    async def unsubscribe_from_match_state_channel(redis_instance: Any, match_id: str) -> None:
        '''Unsubscribe from the match state channel'''
        logger.info(f"Unsubscribing from match state channel for match {match_id}")
        channel = KeyCreation.create_match_session_key(match_id, MatchSessionFields.STATE)
        await PubSubManager.unsubscribe_from_channel(redis_instance, channel)
