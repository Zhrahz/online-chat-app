from django_filters import rest_framework as filters
from apps.chat.models import Chat

class ChatFilter(filters.FilterSet):
    is_group = filters.BooleanFilter(field_name="is_group")

    class Meta:
        model = Chat
        fields = ["is_group"]