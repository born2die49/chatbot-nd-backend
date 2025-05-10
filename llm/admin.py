from django.contrib import admin
from .models import LlmProvider, LlmModel, PromptTemplate


@admin.register(LlmProvider)
class LlmProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('is_active',)


@admin.register(LlmModel)
class LlmModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'model_id', 'is_active', 'created_at')
    search_fields = ('name', 'model_id')
    list_filter = ('provider', 'is_active')


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'created_at')
    search_fields = ('name', 'description', 'template')
    list_filter = ('template_type',)