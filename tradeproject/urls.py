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
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', views.homepage,name='homepage'),
    path('profile/', views.profile_view, name='profile'),
    path('stocks/', views.stock_list_view, name='stock_list'),
    path('stocks/<int:stock_id>/', views.stock_detail_view, name='stock_detail'),
    path('transactions/new/', views.create_transaction_view, name='create_transaction'),
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('watchlist/add/<int:stock_id>/', views.add_to_watchlist_view, name='add_to_watchlist'),
]
