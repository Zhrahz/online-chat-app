from rest_framework import serializers

from apps.account.models import Profile
from apps.chat.models import Message, Chat


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "chat", "message", "timestamp","sender"]
        read_only_fields = ["sender"]
    def validate(self, data):
        sender = self.context["request"].user
        chat = data.get("chat")
        if not chat:
            raise serializers.ValidationError("ایدی چت را وارد کنید")

        if sender not in chat.participants.all():
            raise serializers.ValidationError("شما عضو این چت نیستید و نمی‌توانید پیام ارسال کنید.")

        for participant in chat.participants.exclude(id=sender.id):
            if sender in participant.blacklist.all():
                raise serializers.ValidationError(
                    f"شما بلاک شده‌اید از طرف {participant.username}. نمی‌توانید پیام ارسال کنید.")
        return data

class ChatSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all())
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'name', 'participants', 'messages', 'created', 'is_group']

    def validate(self, data):
        sender = self.context["request"].user
        is_group = self.context['request'].data.get("is_group", False)
        name = self.context["request"].data.get("name")
        participants_list= self.context['request'].data.get("participants", [])

        if not participants_list:
            raise serializers.ValidationError("حداقل یک شرکت‌کننده باید انتخاب شود.")

        for participant_id in participants_list:
            participant = Profile.objects.filter(id=participant_id).first()
            if not participant:
                raise serializers.ValidationError(f"کاربری با شناسه {participant_id} یافت نشد.")
            if sender in participant.blacklist.all():
                raise serializers.ValidationError(f"شما بلاک شده اید از طرف  {participant.username} . نمیتوانید پیام ارسال کنید.")

        if not is_group:
            if len(participants_list) > 1:
                raise serializers.ValidationError("چت خصوصی نمی‌تواند بیش از دو شرکت‌کننده داشته باشد.")
            participant = Profile.objects.filter(id=participants_list[0]).first()
            if participant:
                data["name"] = participant.username
            data["is_group"] = False

        if is_group and len(participants_list) > 1:
            if not name :
                raise serializers.ValidationError("نام چت را وارد کنید")
            data["is_group"] = True

        return data

class ChatFavoriteSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def validate_id(self, value):
        if not Chat.objects.filter(id=value).exists():
            raise serializers.ValidationError("چت با این ایدی موجود نیست")
        return value

class AddParticipantsToChatSerializer(serializers.Serializer):
    participants = serializers.ListField(
        child=serializers.UUIDField(format='hex_verbose'), allow_empty=False
    )
    id = serializers.IntegerField()

    def validate_participants(self, value):
        for participant_id in value:
            if not Profile.objects.filter(id=participant_id).exists():
                raise serializers.ValidationError(f"کاربر با UUID {participant_id} وجود ندارد.")
        return value
    def validate_id(self, value):
        if not Chat.objects.filter(id=value).exists():
            raise serializers.ValidationError("چت با این ایدی موجود نیست")
        return value


