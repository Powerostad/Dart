from django.urls import path
from apps.forex import views

app_name = 'forex'

urlpatterns = [
    path("signals/", views.SignalView.as_view(), name="signals"),
]