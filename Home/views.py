from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from .models import Register
from .serializers import RegisterSerializer
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

        if email is None or not email.strip():
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(email)
        except ValidationError:
            return Response({"detail": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST)

        if Register.objects.filter(email=email).exists():
            return Response({"detail": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp = generate_otp()
            set_otp(email, otp, "signup")
            send_otp_email(email, otp)
        except Exception as e:
            return Response({"detail": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "OTP sent to email."}, status=status.HTTP_200_OK)


class VerifySignupView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"detail": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        cached_otp = get_otp(email, "signup")
        if not cached_otp or cached_otp != otp:
            return Response({"detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            delete_otp(email, "signup")
            user = Register.objects.get(email=email)
            tokens = get_tokens(user)
            return Response({"detail": "Signup successful.", "tokens": tokens}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({"detail": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)

        try:
            otp = generate_otp()
            set_otp(email, otp, "login")
            send_otp_email(email, otp)
            return Response({"detail": "OTP sent to email."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Failed to send OTP: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        password = request.data.get("password")

        if not email or not otp or not password:
            return Response({"detail": "Email, OTP, and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        cached_otp = get_otp(email, "login")
        if not cached_otp or cached_otp != otp:
            return Response({"detail": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if not check_password(password, user.password):
            return Response({"detail": "Incorrect password."}, status=status.HTTP_401_UNAUTHORIZED)

        delete_otp(email, "login")

        tokens = get_tokens(user)
        return Response({
            "tokens": tokens,
            "user": {
                "name": user.name,
                "dob": user.dob,
                "height": user.height,
                "gender": user.gender
            }
        }, status=status.HTTP_200_OK)




@api_view(['DELETE'])
def delete_user_by_email(request, email):
    try:
        user = Register.objects.get(email=email)
        user.delete()
        return Response({"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Register.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
