from django.urls import path
from .views import (
    BlogCreateView, BlogListView, BlogSearchView,
    BlogUpdateView, BlogDeleteView, UserBlogsView
)

app_name='blog'

urlpatterns = [
    path('create/', BlogCreateView.as_view(), name='blog-create'),
    path('', BlogListView.as_view(), name='blog-list'),
    path('search/', BlogSearchView.as_view(), name='blog-search'),
    path('<int:pk>/update/', BlogUpdateView.as_view(), name='blog-update'),
    path('<int:pk>/delete/', BlogDeleteView.as_view(), name='blog-delete'),
    path('my-blogs/', UserBlogsView.as_view(), name='user-blogs'),
]
