from django_filters import rest_framework as filters
from apps.account.models import Profile

class ProfileFilter(filters.FilterSet):
    username = filters.CharFilter(field_name='username', lookup_expr='icontains')
    first_name = filters.CharFilter(field_name='first_name', lookup_expr='icontains')
    last_name = filters.CharFilter(field_name='last_name', lookup_expr='icontains')

    class Meta:
        model = Profile
        fields = ['username', 'first_name', 'last_name']
