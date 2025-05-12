from rest_framework import generics, permissions
from useraccount.serializers import UserProfileSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve and update the authenticated user's profile.
    
    * GET /profile/ - Retrieve user profile
    * PUT /profile/ - Update entire profile
    * PATCH /profile/ - Partially update profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """
        Return the authenticated user as the object to be retrieved/updated.
        """
        return self.request.user