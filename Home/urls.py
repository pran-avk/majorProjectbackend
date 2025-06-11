from django.urls import path
from .views import SignupRequestView, VerifySignupView, LoginRequestView, VerifyLoginView

urlpatterns = [
    path('signup/', SignupRequestView.as_view(), name='signup-request'),
    path('verify-signup/', VerifySignupView.as_view(), name='verify-signup'),
    path('login/', LoginRequestView.as_view(), name='login-request'),
    path('verify-login/', VerifyLoginView.as_view(), name='verify-login'),
]
