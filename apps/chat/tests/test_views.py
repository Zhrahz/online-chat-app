from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.account.models import Profile
from apps.chat.models import Chat, Message


class ChatAPIViewTest(APITestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(username='user', password='password')
        self.participant1 = Profile.objects.create_user(username='user1', password='password1')
        self.participant2 = Profile.objects.create_user(username='user2', password='password2')
        self.blocked_user = Profile.objects.create_user(username='user3', password='password3')

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        refresh1 = RefreshToken.for_user(self.blocked_user)
        self.token_blocked_user = str(refresh1.access_token)

    def test_permission(self, methods=("get", "post"), data=None):
        url = reverse('chat')
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

    def test_create_chat_is_group_false(self):
        url = reverse('chat')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {
            "participants": [str(self.participant1.id)],
            "is_group":False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chat.objects.first().name, self.participant1.username)

        data ={
               "participants": [
                    str(self.participant1.id),
                    str(self.participant2.id)
               ],
               "is_group":False
               }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_chat_is_group_true(self):
        url = reverse('chat')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {
            "name":"test_group",
            "participants": [
                    str(self.participant1.id),
                    str(self.participant2.id)
            ],
            "is_group":True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chat.objects.first().name, "test_group")
        self.assertEqual(Chat.objects.first().create_by, self.user)

    def test_blocked_user(self):
        url = reverse('blacklist')
        data = {"username": self.user.username}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_blocked_user}")
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('chat')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {
                "name": "TEST_CHAT",
                "participants":str(self.blocked_user.id),
                "is_group":False
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_chats(self):
        url = reverse('chat')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class MessageAPIViewTest(APITestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(username='user', password='password')
        self.user1 = Profile.objects.create_user(username='user_1', password='password')
        self.participant1 = Profile.objects.create_user(username='user1', password='password')
        self.blocked_user = Profile.objects.create_user(username='user2', password='password2')

        self.chat = Chat.objects.create(name="test_chat", create_by= self.user, is_group=False)
        self.chat.participants.add(self.user.id, self.participant1.id)
        self.blocked_chat = Chat.objects.create(name="test_chat1",create_by= self.user, is_group=False)
        self.blocked_chat.participants.add(self.user, self.blocked_user)

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        refresh1 = RefreshToken.for_user(self.blocked_user)
        self.token_blocked_user = str(refresh1.access_token)

        refresh2 = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh2.access_token)

    def test_permission(self, method="post", data=None):
        request_method = getattr(self.client, method)
        url = reverse('message')

        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = request_method(url, data)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return response

    def test_send_message_to_chat(self):
        url = reverse('message')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {
            "chat":self.chat.id,
            "message": "Hello!",
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(Message.objects.first().message, "Hello!")

    def test_send_message_blocked_user(self):
        url = reverse('blacklist')
        data = {"username": self.user.username}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_blocked_user}")
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        url = reverse('message')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {
            "chat":self.blocked_chat.id,
            "message": "test message"
                }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_message_to_chat_not_member(self):
        url = reverse('message')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")

        data = {
            "chat": self.chat.id,
            "message": "Hello!",
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class AddParticipantsToChatTest(APITestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(username='user', password='password')
        self.user1 = Profile.objects.create_user(username='user_1', password='password')
        self.participant1 = Profile.objects.create_user(username='user1', password='password')
        self.participant2 = Profile.objects.create_user(username='user2', password='password')
        self.participant3 = Profile.objects.create_user(username='user3', password='password')

        self.chat = Chat.objects.create(name="test_chat", create_by=self.user, is_group=True)
        self.chat.participants.add(self.user, self.participant1 , self.participant2 )

        self.chat1 = Chat.objects.create(name="test_chat1", create_by=self.user, is_group=False)
        self.chat.participants.add(self.user, self.participant1, self.participant2)

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        refresh1 = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh1.access_token)

    def test_permission(self, method="post", data=None):
        request_method = getattr(self.client, method)
        url = reverse('add_participants')

        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")
        response = request_method(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = request_method(url, data)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        return response

    def test_add_participants_to_chat(self):
        url = reverse('add_participants')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {
            "id":self.chat.id,
            "participants":[str(self.participant3.id)]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # print(Chat.objects.first().participants,)
        # print(self.chat.participants.values_list('id', flat=True))
        # print(list(self.chat.participants.values_list('id', flat=True)))
        # print([str(participant_id) for participant_id in self.chat.participants.values_list('id', flat=True)])
        self.assertEqual(sorted(list(self.chat.participants.values_list('id', flat=True))), sorted([self.user.id, self.participant1.id , self.participant2.id, self.participant3.id]))

    def test_add_participants_to_chat_not_member(self):
        url = reverse('add_participants')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")

        data = {
            "id": self.chat.id,
            "participants": [str(self.participant3.id)]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_participants_to_chat_private(self):
        url = reverse('add_participants')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        data = {
            "id": self.chat1.id,
            "participants": [str(self.participant1.id)]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    class FavoriteChatListAPIViewTest(APITestCase):
        def setUp(self):
            self.user = Profile.objects.create_user(username='user', password='password')
            self.user1 = Profile.objects.create_user(username='user1', password='password')
            self.user2 = Profile.objects.create_user(username='user2', password='password')
            self.chat = Chat.objects.create(name="test_chat", create_by=self.user, is_group=False)
            self.chat.participants.add(self.user, self.user1)

            refresh = RefreshToken.for_user(self.user)
            self.token = str(refresh.access_token)

            refresh1 = RefreshToken.for_user(self.user2)
            self.token1 = str(refresh1.access_token)

        def test_add_chat_favorite(self):
            url = reverse('favorite')
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
            data = {
                "id":self.chat.id,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(self.user.favorites.count(), 1)

        def test_add_chat_favorite_not_member(self):
            url = reverse('favorite')
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")
            data = {
                "id":self.chat.id,
            }
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        def test_add_chat_unfavorite(self):
            url = reverse('favorite')
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
            data = {
                "id":self.chat.id,
            }
            response = self.client.delete(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(self.user.favorites.count(), 0)

        def test_add_chat_unfavorite_not_member(self):
            url = reverse('favorite')
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token1}")
            data = {
                "id":self.chat.id,
            }
            response = self.client.delete(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        def test_get_chats_favorite(self):
            url = reverse('favorite')
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
            response = self.client.get(url, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

class ListChatFilterAPIViewTest(APITestCase):
    def setUp(self):
        self.user = Profile.objects.create_user(username='user', password='password')
        self.user1 = Profile.objects.create_user(username='user1', password='password')
        self.user2 = Profile.objects.create_user(username='user2', password='password')

        self.chat_private = Chat.objects.create(name="test_chat", create_by=self.user, is_group=False)
        self.chat_private.participants.add(self.user, self.user1)
        self.chat_group = Chat.objects.create(name="test_chat1", create_by=self.user, is_group=True)
        self.chat_group.participants.add(self.user, self.user2, self.user1 )

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def test_list_chat_group_filter(self):
        url = reverse('filter')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get(url, {'is_group': 'true'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], self.chat_group.name)

    def test_list_chat_private_filter(self):
        url = reverse('filter')
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")
        response = self.client.get(url, {'is_group': 'false'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], self.chat_private.name)