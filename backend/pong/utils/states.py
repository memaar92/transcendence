class UserOnlineStatus:
    ONLINE = "online"
    IN_QUEUE = "in_queue"
    PLAYING = "playing"
    OFFLINE = "offline"

class MatchState:
    REGISTERING = "registering"     # Registering players, until the match is full
    INITIALIZING = "initializing"   # Initializing the match, until the match starts
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    CANCELLED = "cancelled"