from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import CustomUser, Profile
from .serializers import UserSerializer, ProfileSerializer, GroupSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .forms import CustomRegistrationForm
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            error_message = "Invalid credentials"
    else:
        error_message = None
    return render(request, 'login.html', {'error_message': error_message})

class ProfileView(APIView):

    def get(self, request, *args, **kwargs):
        result = Profile.objects.all()
        serializers = ProfileSerializer(result, many=True)
        return Response({'status': 'success', "profile": serializers.data}, status=200)
    
    
    def post(self, request):
        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get(id=kwargs['id'])
        except Profile.DoesNotExist:
            return Response({"status": "error", "data": "profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "data": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, *args, **kwargs):
        try:
            profile = Profile.objects.get(id=kwargs['id'])
        except Profile.DoesNotExist:
            return Response({"status": "error", "data": "profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        profile.delete()
        return Response({"status": "success", "data": "profile deleted"}, status=status.HTTP_200_OK)
    
class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Profile.objects.all().order_by('id')
    serializer_class = ProfileSerializer

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

class RegistrationAPIView(APIView):
    # This class verifies the Firebase token and sets request.user
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # We pass the already authenticated user (from the token) 
        # and the extra data (DoB, campus, etc.) to the form
        form = CustomRegistrationForm(request.data, instance=request.user)
        
        if form.is_valid():
            user = form.save()
            return Response({
                "message": "User profile synced successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    # Add any profile fields you want to return to React here
                }
            }, status=status.HTTP_200_OK)
            
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "groups": [group.name for group in user.groups.all()]
        })

class GroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = request.user.groups.all()  # Get user groups
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
    
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = UserSerializer