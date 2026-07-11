from django_redis import get_redis_connection
import json

def register_data(data):

    redis_instance = get_redis_connection("default")
    key = f"account:data:{data.get('email')}"
    redis_instance.set(key, json.dumps(data), ex=300)