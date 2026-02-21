import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "123:fake-token")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
MEILISEARCH_URL = os.getenv("MEILISEARCH_URL", "http://localhost:7700")
MEILISEARCH_KEY = os.getenv("MEILISEARCH_KEY", "masterKey")
