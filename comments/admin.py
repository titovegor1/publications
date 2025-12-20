from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']
    list_filter = ['created_at', 'user']
    search_fields = ['text', 'user__username', 'post__title']
    date_hierarchy = 'created_at'
