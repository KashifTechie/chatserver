import random

def generate_otp():
    """Generate a 6-digit OTP."""
    otp = str(random.randint(100000, 999999))
    return otp