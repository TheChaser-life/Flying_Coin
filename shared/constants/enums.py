from enum import Enum

class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "production"

class Granularity(str, Enum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"

class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class QueueName(str, Enum):
    MARKET_DATA = "market_data_queue"
    PREDICTION_TASKS = "prediction_tasks_queue"
    SENTIMENT_TASKS = "sentiment_tasks_queue"
    NOTIFICATIONS = "notifications_queue"
