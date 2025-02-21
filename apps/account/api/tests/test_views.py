import requests

from apps.account.models import Profile

from django.urls import reverse
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterViewTest (TestCase):
    def setUp(self):
        self.client = Client()

    def test_user_create(self):
        response = self.client.post('/account/register/', {'username': 'user', 'password': 'password', "confirm_password": "password"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Profile.objects.filter(username='user').exists())
    def test_without_confirm_password(self):
        response = self.client.post('/account/register/', {'username': 'user1', 'password': 'password1'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    def test_invalid_confirm_password(self):
        response = self.client.post('/account/register/', {'username': 'user', 'password': 'password', "confirm_password": "<PASSWORD>"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UpdateProfileViewTest (APITestCase):
    def setUp(self) -> None:
        self.user = Profile.objects.create(username='user1', password='password1')
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        image_response = requests.get("https://sample-videos.com/img/Sample-jpg-image-50kb.jpg")
        if image_response.status_code == 200:
            self.dummy_image = SimpleUploadedFile(
                "Sample-jpg-image-50kb.jpg",
                image_response.content,
                content_type=image_response.headers.get("Content-Type", "image/jpeg"),
            )
        else:
            raise ValueError("تصویر بارگیری نشد!")

    def test_permission(self, method="put", data=None):
        request_method = getattr(self.client, method)
        url = reverse('edit-profile', kwargs={'pk': self.user.pk})

        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = request_method(url, data)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return response

    def test_update(self):
        url = reverse('edit-profile', kwargs={'pk': self.user.pk})

        data = {
            "first_name": "EDIT_NAME",
            "description": "EDIT_DESCRIPTION",
            "image": self.dummy_image,
        }

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.put(url, data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        result = response.json()
        self.assertEqual(result["first_name"], data["first_name"])
        self.assertEqual(result["description"], data["description"])

class ProfileListViewTest (APITestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(username='user1', password='password1')
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def test_permission(self, method="get", data=None):
        request_method = getattr(self.client, method)
        url = reverse('profile')

        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = request_method(url, data)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return response

    def test_profile_list(self):
        url = reverse('profile')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
        self.assertIn("username", response.data[0])

class LogoutUserViewTest(APITestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(
            username="testuser", password="testpassword123"
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def test_permission(self, method="post", data=None):
        request_method = getattr(self.client, method)
        url = reverse('logout')

        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = request_method(url, data)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return response

    def test_logout_user(self):
        refresh = RefreshToken.for_user(self.user)
        url = reverse('logout')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {"refresh": str(refresh), "username": self.user.username, "password": "testpassword123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "You are logged out.")

class BlackListAPIViewTest(APITestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(
            username="testuser", password="testpassword123"
        )
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.other_user = Profile.objects.create_user(
            username="blockeduser", password="testpassword123"
        )

    def test_permission(self, methods=("get", "post", "delete"), data=None):
        url = reverse('blacklist')
        for method in methods:
            request_method = getattr(self.client, method)

            response = request_method(url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
            response = request_method(url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
            response = request_method(url, data)
            self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            return response

    def test_block_user(self):
        url = reverse('blacklist')
        data = {"username": self.other_user.username}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.other_user, self.user.blacklist.all())

    def test_unblock_user(self):
        self.user.blacklist.add(self.other_user)
        url = reverse('blacklist')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {"username": self.other_user.username}
        response = self.client.delete(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn(self.other_user, self.user.blacklist.all())