from django.urls import path
from . import views
from .views import get_users_with_unread

urlpatterns = [
    path('', views.signup_desh, name='signup_desh'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('signup_desh/', views.signup_desh, name='signup_desh'),
    path('home/', views.home, name='home'),
    path('chat/', views.chat, name='chat'),
    path('logout_view/', views.logout_view, name='logout_view'),
    path('get-messages/<int:user_id>/', views.get_messages, name='get_messages'),
    path('send-message/', views.send_message, name='send_message'),
    path('show_logs/', views.show_logs, name='show_logs'),
    path('get_users_with_unread/', get_users_with_unread, name='get_users_with_unread'),
    path('users-with-unread/', get_users_with_unread, name='users_with_unread'),
    path('set-typing/', views.set_typing, name='set_typing'),
    path('get-typing/<int:user_id>/', views.get_typing, name='get_typing'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/stats/', views.admin_stats, name='admin_stats'),
    path('admin/users/', views.admin_users, name='admin_users'),
]
