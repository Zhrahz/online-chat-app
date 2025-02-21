from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.account.models import Profile
from apps.chat.models import Chat, Message
from apps.chat.api.filters.chat import ChatFilter
from apps.chat.api.serializers.chat import ChatSerializer, MessageSerializer, ChatFavoriteSerializer, \
    AddParticipantsToChatSerializer


class ChatAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        chats = Chat.objects.annotate(last_message_time=Max('messages__timestamp')).order_by('-last_message_time')
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ChatSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            is_group = serializer.validated_data.get('is_group')
            chat_name = serializer.validated_data.get('name')
            participants = serializer.validated_data.get('participants',[])
            create_by = request.user

            chat = Chat.objects.create(name=chat_name, create_by=create_by, is_group=is_group)
            chat.participants.add(*participants)
            chat.participants.add(create_by)

            return Response({"detail": "چت ساخته شد."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListChatFilterAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatSerializer
    queryset = Chat.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_group']
    filterset_class = ChatFilter

class MessageAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            message_content = request.data.get('message')
            chat_id = request.data.get('chat')
            chat = request.user.chats.filter(id=chat_id).first()
            is_group = chat.is_group
            chat_name = chat.name

            if is_group is False :
                sender = request.user.username
                participant = Profile.objects.exclude(id=request.user.id).first()
                if sender == chat_name:
                    chat_name = participant.username
            if chat :
                message = Message.objects.create(
                chat=chat,
                sender=request.user,
                message=message_content,)
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"chat_{chat_id}",
                    {
                        "type": "chat_message",
                        "message": f"{user.username}: {message_content}, Chat_Name: {chat_name}, Chat_id: {chat_id}"
                    }
                )
            else:
                return Response(
                    {"detail": "چت یافت نشد یا شما عضو این چت نیستید."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response(
                {"detail": "پیام ارسال شد.", "message": MessageSerializer(message).data, "chat": chat_name},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddParticipantsToChat(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = AddParticipantsToChatSerializer(data=request.data)
        if serializer.is_valid():
            chat_id = request.data.get('id')
            chat = Chat.objects.filter(id=chat_id).first()
            is_group = chat.is_group
            if is_group is True:
                participants = request.data.get('participants')
                for participant in participants:
                    if chat.participants.filter(id=participant).exists():
                        return Response({"این فرد عضو گروه هست"})
                    if chat.participants.filter(id=request.user.id).exists():
                        chat.participants.add(*participants)
                        return Response({"detail":"به گروه اضافه شد."}, status=status.HTTP_200_OK)
                    return Response({"detail":"شما عضو گروه نیستید."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail":"این چت شخصی است و شما امکان اضافه کردن کاربر را ندارین"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class FavoriteChatListAPIView(APIView) :
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        favorite_chats = request.user.favorits.all()
        serializer = ChatFavoriteSerializer(favorite_chats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self,request) :
        serializer =  ChatFavoriteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            chat_id = request.data.get('id')
            chat = Chat.objects.filter(id=chat_id).first()
            if request.user in chat.participants.all():
                request.user.favorits.add(chat)
                return Response({"detail": "چت به علاقه مندی ها اضافه شد."}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "شما عضو این چت نیستید."},status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        serializer = ChatFavoriteSerializer(data=request.data)
        if serializer.is_valid():
            chat_id = request.data.get('id')
            chat = Chat.objects.filter(id=chat_id).first()
            if request.user in chat.participants.all():
                request.user.favorits.remove(chat)
                return Response({"detail": "چت از علاقه مندی ها حذف شد."}, status=status.HTTP_200_OK)
            else:
                return Response({"detail": "شما عضو این چت نیستید."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)