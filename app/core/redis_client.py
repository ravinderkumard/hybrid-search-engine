import redis.asyncio as redis


redis_client = redis.Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=False,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
)