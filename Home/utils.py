import random
from django.core.mail import send_mail
from django.core.cache import cache

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    send_mail(
        subject='Your OTP Code',
        message=f'Your OTP is: {otp}',
        from_email='yourapp@example.com',
        recipient_list=[email],
        fail_silently=False,
    )

def set_otp(email, otp, purpose, ttl=300):  # 5 minutes = 300 seconds
    cache_key = f"{purpose}_otp_{email}"
    cache.set(cache_key, otp, timeout=ttl)

def get_otp(email, purpose):
    cache_key = f"{purpose}_otp_{email}"
    return cache.get(cache_key)

def delete_otp(email, purpose):
    cache_key = f"{purpose}_otp_{email}"
    cache.delete(cache_key)
