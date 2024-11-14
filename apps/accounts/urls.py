from django.urls import path,include
from apps.accounts import views
from . import views
from rest_framework.routers import DefaultRouter
from .views import UserDetailView, ProfileDetailView, UserRegisterView, UserLoginView, UserLogoutView, profile_view,UserViewSet

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
    # profile views
    path('profile/', views.profile_view, name='profile'),
    #path('profiles/', ProfileListCreateView.as_view(), name='profile-list-create'),
    #path('users/', views.UserViewSet.as_view(), name='user-list-create'),
    # Include router URLs
    path('', include(router.urls)),
]

# Include router urls
urlpatterns += router.urls