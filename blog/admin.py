from django.contrib import admin
from .models import Post, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'description']
    list_filter = ['author']
    search_fields = ['title', 'description', 'author__username']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'pub_date']
    list_filter = ['pub_date', 'author', 'categories']
    search_fields = ['title', 'text']
    filter_horizontal = ['categories']
    date_hierarchy = 'pub_date'
