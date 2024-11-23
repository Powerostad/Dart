from django.urls import path,include
from apps.accounts import views
from rest_framework_simplejwt import views as jwt_views

from .views import GoogleCallbackView, GoogleAuthRedirectView

urlpatterns = [
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path('profile/', views.ProfileView.as_view(), name='profile'),

    path("token/", jwt_views.TokenObtainPairView.as_view(), name='token'),
    path("token/refresh/", jwt_views.TokenRefreshView.as_view(), name='token-refresh'),

    path('google/login/', GoogleAuthRedirectView.as_view(), name='google-login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google-callback'),

]
