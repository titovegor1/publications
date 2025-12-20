from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/create/', views.post_create, name='post_create'),
    path('category/<int:pk>/', views.category_posts, name='category_posts'),
    path('category/create/', views.category_create, name='category_create'),
    path('user/<int:pk>/', views.user_posts, name='user_posts'),
    path('search/', views.search, name='search'),
]
