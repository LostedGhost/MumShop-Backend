from django.urls import path
from apps.views import *

urlpatterns = [
    path('register/', register_user, name='register_user'),
    path('login/', login_user, name='login_user'),
    path('logout/', logout_user, name='logout_user'),
    path('users/', get_users, name='get_users'),
    path('me/', get_connected_user, name='get_connected_user'),
    path('me/update/', update_user, name='update_user'),
    
    path('supermarket/<str:supermarket_slug>/', get_supermarket, name='get_supermarket'),
    path('supermarkets/', list_supermarkets, name='list_supermarkets'),
    path('seller/supermarket/add/', create_supermarket, name='create_supermarket'),
    path('seller/supermarket/<str:supermarket_slug>/alter/', alter_supermarket, name='alter_supermarket'),
    path('seller/supermarket/<str:supermarket_slug>/delete/', delete_supermarket, name='delete_supermarket'),
    
    path('categories/', list_categories, name='list_categories'),
    path('category/add/', add_category, name='add_category'),
    path('category/<str:category_slug>/alter/', alter_category, name='alter_category'),
    path('category/<str:category_slug>/', get_category, name='get_category'),
    path('category/<str:category_slug>/delete/', delete_category, name='delete_category'),
    
    
]