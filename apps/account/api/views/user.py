
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.generics import UpdateAPIView, CreateAPIView, ListAPIView


from apps.account.models import Profile
from apps.account.api.filters.user import ProfileFilter
from apps.account.api.serializers.user import RegisterUserSerializer, ProfileSerializer, BlackListSerializer, \
    UserListSerializer, LogoutSerializer


class RegisterUserView(CreateAPIView):
    permission_classes = AllowAny,
    serializer_class = RegisterUserSerializer

class UpdateProfileView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = [MultiPartParser]
    queryset = Profile.objects.all()
    authentication_classes = (JWTAuthentication,)
    serializer_class = ProfileSerializer

class ProfileListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserListSerializer
    queryset = Profile.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'first_name', 'last_name']
    filterset_class = ProfileFilter

class LogoutUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            Refresh_token = request.data.get("refresh")
            token = RefreshToken(Refresh_token)
            username = request.data.get("username")
            password = request.data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None and token :
                token.blacklist()
                return Response('You are logged out.' ,status=status.HTTP_200_OK)
            else:
                return Response('The username or password is incorrect.')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BlackListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        blocked_users = request.user.blacklist.all()
        serializer = BlackListSerializer(blocked_users, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = BlackListSerializer(data=request.data)
        if serializer.is_valid():
            user = request.data.get("username")
            user_to_block = Profile.objects.filter(username=user).first()
            if user_to_block:
                request.user.blacklist.add(user_to_block)
                return Response({"detail": f"{user_to_block.username} بلاک شد."}, status=status.HTTP_200_OK)
            return Response("این کاربر وجود ندارد")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request):
        serializer = BlackListSerializer(data=request.data)
        if serializer.is_valid():
            user = request.data.get("username")
            user_to_block = Profile.objects.filter(username=user).first()
            if user_to_block:
                request.user.blacklist.remove(user_to_block)
                return Response({"detail": f"{user_to_block.username} انبلاک شد."}, status=status.HTTP_200_OK)
            return Response("این کاربر وجود ندارد")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)