"""
URL configuration for tradeproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.accounts import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from allauth.account import views as allauth_views

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path("api/accounts/", include("apps.accounts.urls")),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # path("", include("apps.dashboard.urls", namespace="main")),
    # path('accounts/login/', allauth_views.LoginView.as_view(), name='account_login'),
    #
    # path('accounts/logout/', allauth_views.LogoutView.as_view(), name='account_logout'),
    # path('accounts/signup/', allauth_views.SignupView.as_view(), name='account_signup'),
    # # path('', views.homepage,name='homepage'),
    # path('profile/', views.profile_view, name='profile'),
    # path('stocks/', views.stock_list_view, name='stock_list'),
    # path('stocks/<int:stock_id>/', views.stock_detail_view, name='stock_detail'),
    # path('transactions/new/', views.create_transaction_view, name='create_transaction'),
    # path('watchlist/', views.watchlist_view, name='watchlist'),
    # path('watchlist/add/<int:stock_id>/', views.add_to_watchlist_view, name='add_to_watchlist'),
    # path('accounts/password/change/', auth_views.PasswordChangeView.as_view(template_name='account/password_change.html'), name='password_change'),
    # path('accounts/password/change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='account/password_change_done.html'), name='password_change_done'),
    # path('accounts/password/reset/', auth_views.PasswordResetView.as_view(template_name='account/password_reset.html'), name='password_reset'),
    # path('accounts/password/reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'), name='password_reset_done'),
    # path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'), name='password_reset_confirm'),
    # path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='account/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)