from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ["position", "photo"]


class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = UserAdmin.list_display + ("position",)
    list_filter = UserAdmin.list_filter + ("profile__position",)

    @admin.display(description="Position")
    def position(self, obj):
        return getattr(obj.profile, "position", "") if hasattr(obj, "profile") else ""


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
