from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'display_name', 'discord_id', 'reputation_score', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Discord', {'fields': ('discord_id', 'display_name', 'reputation_score')}),
    )
