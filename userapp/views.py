from django.db import transaction 
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from .models import CustomUser, Profile
from .serializers import UserSerializer, ProfileSerializer, GroupSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from .forms import CustomRegistrationForm
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import Group


class ProfileView(APIView):
    permission_classes = [IsAuthenticated] 

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

    def get_object(self):
        print(f"DEBUG: Looking up Profile with user_id={self.kwargs['pk']}")
        return get_object_or_404(Profile, user_id=self.kwargs['pk'])

    def update(self, request, *args, **kwargs):
        print(f"DEBUG: Update request data: {request.data}")
        try:
            return super().update(request, *args, **kwargs)
        except Exception as e:
            print(f"DEBUG: Error during update: {e}")
            raise


class RegistrationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        form = CustomRegistrationForm(request.data, instance=request.user)
        if not form.is_valid():
            return Response(form.errors, status=400)

        try:
            with transaction.atomic():
                user = form.save()
        except Exception as e:
            return Response(
                {"detail": "Profile creation failed. Please try again.", "error": str(e)},
                status=500
            )

        return Response({"user": UserSerializer(user).data}, status=201)


class UsernameCheckAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        username = request.query_params.get("username", "").strip()

        if not username:
            return Response({"error": "No username provided."}, status=400)

        if len(username) < 3:
            return Response({"available": False, "reason": "Username must be at least 3 characters."})

        if len(username) > 30:
            return Response({"available": False, "reason": "Username must be 30 characters or fewer."})

        exists = CustomUser.objects.filter(username__iexact=username).exists()
        return Response({"available": not exists})


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
        groups = Group.objects.all()  # Get ALL groups instead of user.groups.all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all().order_by('id')
    serializer_class = UserSerializer