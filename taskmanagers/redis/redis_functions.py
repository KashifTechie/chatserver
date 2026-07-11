from django.core.cache import cache
from taskmanagers.redis.redis_keys import account_otp_key

def set_register_otp(email, otp, timeout=300):
    key = account_otp_key(email)
    cache.set(key, otp, timeout)

def get_register_otp(email):
    key = account_otp_key(email)
    return cache.get(key)

def delete_register_otp(email):
    key = account_otp_key(email)
    cache.delete(key)
