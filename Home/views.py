from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Register
from .serializers import RegisterSerializer
from django.contrib.auth.hashers import make_password, check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import generate_otp, send_otp_email, set_otp, get_otp, delete_otp
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def get_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
class SignupRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")

        # 1. Check if email is missing
        if email is None:
            return Response({"detail": "Email field is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check if email is an empty string
        if not email.strip():
            return Response({"detail": "Email cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Check if email format is invalid
        try:
            validate_email(email)
        except ValidationError:
            return Response({"detail": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Check if email already exists
        if Register.objects.filter(email=email).exists():
            return Response({"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

        # 5. If all checks pass, generate and send OTP
        try:
            otp = generate_otp()
            set_otp(email, otp, "signup")
            send_otp_email(email, otp)
        except Exception as e:
            return Response({"detail": f"Failed to send OTP. Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "OTP sent to email."}, status=status.HTTP_200_OK)



class VerifySignupView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        # Validate email and OTP fields
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not otp:
            return Response({"detail": "OTP is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if OTP is valid
        cached_otp = get_otp(email, "signup")
        if not cached_otp:
            return Response({"detail": "OTP expired or not requested."}, status=status.HTTP_400_BAD_REQUEST)
        if cached_otp != otp:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and save user data
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # Save with hashed password
            serializer.save(password=make_password(serializer.validated_data['password']))

            # Clear OTP
            delete_otp(email, "signup")

            # Get saved user and generate tokens
            user = Register.objects.get(email=email)
            tokens = get_tokens(user)

            return Response({
                "detail": "Signup successful.",
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)

        # Return validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")

        # Check for missing email
        if not email:
            return Response({"detail": "Email is required."}, status=400)

        # Check if user exists
        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({"detail": "User with this email does not exist."}, status=404)

        # Generate and send OTP
        try:
            otp = generate_otp()
            set_otp(email, otp, "login")
            send_otp_email(email, otp)
            return Response({"detail": "OTP sent to email."}, status=200)
        except Exception as e:
            return Response({"detail": f"Failed to send OTP: {str(e)}"}, status=500)


class VerifyLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        password = request.data.get("password")

        # Check for missing fields
        if not email or not otp or not password:
            return Response({"detail": "Email, OTP, and password are required."}, status=400)

        # Retrieve OTP from cache
        cached_otp = get_otp(email, "login")
        if not cached_otp:
            return Response({"detail": "OTP has expired or was not requested."}, status=400)

        if cached_otp != otp:
            return Response({"detail": "Invalid OTP."}, status=400)

        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({"detail": "User not found."}, status=404)

        if not check_password(password, user.password):
            return Response({"detail": "Incorrect password."}, status=401)

        delete_otp(email, "login")
        return Response(get_tokens(user), status=200)