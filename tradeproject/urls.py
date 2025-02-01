from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.static import serve

from apps.accounts import views
from django.conf import settings
from django.conf.urls.static import static


static_urlpatterns = [
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
]


urlpatterns = [
    path('api/', include([
        path('dashboard/', include('apps.dashboard.urls', namespace='dashboard')),
        path('accounts/', include('apps.accounts.urls', namespace='accounts')),
        path('chatbot/', include('apps.chatbot.urls', namespace='chatbot')),
        path('forex/', include('apps.forex.urls', namespace='forex')),

        path('docs/', TemplateView.as_view(template_name="index.html"), name="swagger-ui"),

        path('blog/', include('apps.blog.urls', namespace='blog')),

    ])),
    path("", include(static_urlpatterns)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)