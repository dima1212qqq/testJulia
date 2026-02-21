import taskiq_redis
from taskiq import TaskiqScheduler
from taskiq_redis import ListQueueBroker
from app.config import REDIS_URL

# Using ListQueueBroker which relies on Redis Lists
broker = ListQueueBroker(
    url=REDIS_URL,
)
