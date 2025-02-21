from apps.account.models import Profile

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.contrib.auth.hashers import make_password


class RegisterUserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(min_length=4, max_length=100, write_only=True)
    class Meta:
        model = Profile
        fields = ['id', 'username', 'password','confirm_password']

    def create(self, validated_data):
        user = Profile.objects.create(
            username=validated_data['username'],
            password=make_password(validated_data['password']))
        return user
    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError("Those passwords don't match.")
        return attrs

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'image', 'description', 'first_name', 'last_name']

    def validate(self, attrs):
        user = self.context['request'].user
        target_user = self.instance

        if user in target_user.blacklist.all():
            raise ValidationError("شما توسط این کاربر بلاک شده اید امکان مشاهده پروفایل را ندارید.")

        return attrs

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'username', 'first_name', 'last_name']

class BlackListSerializer(serializers.Serializer):
    class Meta:
        model = Profile
        fields = ['id', 'username']
        read_only_fields = ['id']

    def validate_username(self, value):
        if not Profile.objects.filter(username=value).exists():
            raise serializers.ValidationError("این کاربر وجود ندارد.")
        return value

class LogoutSerializer(serializers.Serializer):
    class Meta:
        model = Profile
        fields = ['password', 'username', 'refresh']

    def validate_username(self, value):
        if not Profile.objects.filter(username=value).exists():
            raise serializers.ValidationError("این کاربر وجود ندارد.")
        return value

