from django.urls import path, re_path

from apps.dashboard import views


app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='dashboard'),
    re_path(r'^.*\.*', views.pages, name='pages'),
]