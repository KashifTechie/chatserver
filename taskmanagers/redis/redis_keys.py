# from django.core.cache import cache

def account_otp_key(email):
    return f"account:otp:{email}"

def account_data_key(email):
    return f"account:data:{email}"

def x_oauth_code_verifier_key(state):
    return f"x_oauth:code_verifier:{state}"