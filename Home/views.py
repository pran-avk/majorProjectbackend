from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Register
from .serializers import RegisterSerializer
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import generate_otp, send_otp_email, set_otp, get_otp, delete_otp

def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class SignupRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if Register.objects.filter(email=email).exists():
            return Response({"detail": "Email already registered."}, status=400)

        otp = generate_otp()
        set_otp(email, otp, "signup")
        send_otp_email(email, otp)
        return Response({"detail": "OTP sent to email."})


class VerifySignupView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        cached_otp = get_otp(email, "signup")

        if cached_otp != otp:
            return Response({"detail": "Invalid or expired OTP."}, status=400)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(password=make_password(serializer.validated_data['password']))
            delete_otp(email, "signup")
            user = Register.objects.get(email=email)
            return Response(get_tokens(user), status=201)
        return Response(serializer.errors, status=400)


class LoginRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        try:
            user = Register.objects.get(email=email)
            if not check_password(password, user.password):
                raise Exception()
        except:
            return Response({"detail": "Invalid credentials."}, status=401)

        otp = generate_otp()
        set_otp(email, otp, "login")
        send_otp_email(email, otp)
        return Response({"detail": "OTP sent to email."})


class VerifyLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        cached_otp = get_otp(email, "login")

        if cached_otp != otp:
            return Response({"detail": "Invalid or expired OTP."}, status=400)

        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        delete_otp(email, "login")
        return Response(get_tokens(user), status=200)
