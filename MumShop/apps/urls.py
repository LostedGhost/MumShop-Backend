from django.urls import path
from apps import views

urlpatterns = [
    path('register/', views.register_user, name='register_user'),
    path('login/', views.login_user, name='login_user'),
    path('users/', views.get_users, name='get_users'),
]