from django.contrib import admin

from apps.account.models import Profile


# Register your models here.


@admin.register(Profile)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'description')
