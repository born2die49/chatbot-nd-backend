from django.shortcuts import render

from rest_framework import viewsets

from chatbot.vectorstore.models import VectorStoreInstance

# Create your views here.
class VectorStoreInstanceViewSet(viewsets.ModelViewSet):
    # ... other attributes ...
    
    def get_queryset(self):
        """
        Return only vector store instances owned by the authenticated user, ordered by creation date.
        """
        return VectorStoreInstance.objects.filter(user=self.request.user).order_by('-created_at') # Added order_by