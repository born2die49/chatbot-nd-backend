from django.contrib import admin
from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('id', 'message_type', 'content', 'created_at', 'references')
    can_delete = False
    max_num = 0
    fields = ('message_type', 'content', 'created_at', 'references')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'vector_store', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'user')
    search_fields = ('title', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [ChatMessageInline]
    date_hierarchy = 'created_at'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'message_type', 'short_content', 'created_at')
    list_filter = ('message_type', 'created_at', 'session__user')
    search_fields = ('content', 'session__title', 'session__user__username')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
    
    def short_content(self, obj):
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content
    short_content.short_description = 'Content'