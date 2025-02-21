from django.urls import path

from .views.user import LogoutUserView, UpdateProfileView, RegisterUserView, ProfileListView, BlackListAPIView

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('edit/<uuid:pk>/', UpdateProfileView.as_view(), name='edit-profile'),
    path('logout/', LogoutUserView.as_view(), name='logout'),
    path('profile/', ProfileListView.as_view(), name='profile'),
    path('blacklist/', BlackListAPIView.as_view(), name='blacklist'),



]
