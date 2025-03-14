from django.urls import path
from .views import (
    BlogCreateView, BlogListView, BlogSearchView,
    BlogUpdateView, BlogDeleteView, UserBlogsView,
    BlogDetailView, ApproveRejectBlogView, BlogListAdminView
)

app_name='blog'

urlpatterns = [
    path('create/', BlogCreateView.as_view(), name='blog-create'),
    path('', BlogListView.as_view(), name='blog-list'),
    path('search/', BlogSearchView.as_view(), name='blog-search'),
    path('<int:pk>/update/', BlogUpdateView.as_view(), name='blog-update'),
    path('<int:pk>/delete/', BlogDeleteView.as_view(), name='blog-delete'),
    path('my-blogs/', UserBlogsView.as_view(), name='user-blogs'),
    path('<int:pk>/', BlogDetailView.as_view(), name='blog-detail'),  # New API for single blog
    path('<int:pk>/status/', ApproveRejectBlogView.as_view(), name='blog-status-update'),
    path('admin/list/', BlogListAdminView.as_view(), name='admin-blog-list'),
]
