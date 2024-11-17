from django.urls import path,include
from apps.accounts import views
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt import views as jwt_views

from .views import GoogleCallbackView, GoogleAuthRedirectView

# Using DRF's router if you want to use viewsets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.ProfileViewSet, basename='profile')

urlpatterns = [
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    # Profile and User detail views
    path('user/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path("token/", jwt_views.TokenObtainPairView.as_view(), name='token'),
    path("token/refresh/", jwt_views.TokenRefreshView.as_view(), name='token-refresh'),

    path('google/login/', GoogleAuthRedirectView.as_view(), name='google-login'),
    path('google/callback/', GoogleCallbackView.as_view(), name='google-callback'),

    path('', include(router.urls)),
]

# Include router urls
urlpatterns += router.urls