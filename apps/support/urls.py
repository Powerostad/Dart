from django.urls import path
from . import views

urlpatterns = [
    # Create a new support thread
    path('threads/create/', views.CreateSupportThreadView.as_view(), name='create-support-thread'),

    # List all support threads (staff view) or user-specific threads
    path('threads/', views.ListSupportThreadsView.as_view(), name='list-support-threads'),

    # List threads specific to the authenticated user
    path('threads/user/', views.UserSupportThreadsView.as_view(), name='user-support-threads'),

    # Add a new message to a specific thread
    path('threads/<int:thread_id>/messages/add/', views.AddSupportMessageView.as_view(), name='add-support-message'),

    # List all messages in a specific thread
    path('threads/<int:thread_id>/messages/', views.ListThreadMessagesView.as_view(), name='list-thread-messages'),
]
