from django.urls import path
from .views import SignupRequestView, VerifySignupView, LoginRequestView, VerifyLoginView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,    # For login (access + refresh)
    TokenRefreshView,       # For refreshing access token
    TokenVerifyView         # For verifying access token
)

urlpatterns = [
    path('signup/', SignupRequestView.as_view(), name='signup-request'),
    path('verify-signup/', VerifySignupView.as_view(), name='verify-signup'),
    path('login/', LoginRequestView.as_view(), name='login-request'),
    path('verify-login/', VerifyLoginView.as_view(), name='verify-login'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
