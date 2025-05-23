from django.contrib import admin

from vectorstore.models import VectorStoreProvider, EmbeddingModel

# Register your models here.

admin.site.register(VectorStoreProvider)

admin.site.register(EmbeddingModel)