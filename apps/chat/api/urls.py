from django.urls import path

from apps.chat.api.views.chat import ChatAPIView, MessageAPIView, AddParticipantsToChat, FavoriteChatListAPIView, \
    ListChatFilterAPIView

urlpatterns = [
    path('chat/', ChatAPIView.as_view(), name='chat'),
    path('message/', MessageAPIView.as_view(), name='message'),
    path('add_participants/', AddParticipantsToChat.as_view(), name='add_participants'),
    path('favorite/', FavoriteChatListAPIView.as_view(), name='favorite'),
    path('filter/', ListChatFilterAPIView.as_view(), name='filter'),

    ]