import redis

REDIS_INSTANCE = redis.StrictRedis(host='redis', port=6379, db=0)

class RedisKeys:
    USER_SESSION = "user:session"
    MATCHES_OPEN = "matches:open"

class QueueFields:
    MATCHMAKING_QUEUE = "matchmaking_queue"

class MatchSessionFields:
    STATE = "state"
    CREATION_TIME = "creation_time"
    ASSIGNED_USERS = "assigned_users" # List of user IDs assigned to the match
    REGISTERED_USERS = "registered_users" # List of user IDs registered for the match
    CONNECTED_USERS = "connected_users" # List of user IDs connected to the match
    RECONNECTION_ATTEMPTS = "reconnection_attempts"

class UserSessionFields:
    LAST_MATCH_ID = "last_match_id"
    ONLINE_STATUS = "online_status"
    LAST_LOGIN = "last_login"