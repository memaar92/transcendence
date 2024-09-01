import redis.asyncio as redis

REDIS_INSTANCE = redis.Redis(host='redis', port=6379, db=0)

class GeneralChannels:
    NEW_MATCH = "new_match"
    MATCH_FINISHED = "match_finished"

class RedisKeys:
    USER_SESSION = "user:session"
    MATCHES = "matches"

class QueueFields:
    MATCHMAKING_QUEUE = "matchmaking_queue"

class MatchSessionFields:
    STATE = "state"
    CREATION_TIME = "creation_time"
    OUTCOME = "outcome"
    ASSIGNED_USERS = "assigned_users" # List of user IDs assigned to the match
    REGISTERED_USERS = "registered_users" # List of user IDs registered for the match
    CONNECTED_USERS = "connected_users" # List of user IDs connected to the match
    RECONNECTION_ATTEMPTS = "reconnection_attempts"

class MatchState:
    REGISTERING = "registering"     # Registering players, until the match is full
    INITIALIZING = "initializing"   # Initializing the match, until the match starts
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"

class MatchOutcome:
    NORMAL = "normal"
    DRAW = "draw"

class UserSessionFields:
    LAST_MATCH_ID = "last_match_id"
    ONLINE_STATUS = "online_status"
    LAST_LOGIN = "last_login"

class UserGameStatus:
    AVAILABLE = "available"
    IN_QUEUE = "in_queue"
    PLAYING = "playing"
    OFFLINE = "offline"