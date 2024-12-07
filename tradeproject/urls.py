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
from apps.accounts.views import GoogleCallbackView

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
urlpatterns = [
    path('api/', include([
        path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
        path('accounts/', include('apps.accounts.urls', namespace='accounts')),
        path('chatbot/', include('apps.chatbot.urls', namespace='chatbot')),
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    ])),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)