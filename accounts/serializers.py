from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Profile


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Incorrect username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")
        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    name = serializers.SerializerMethodField()
    rank = serializers.IntegerField(read_only=True)

    class Meta:
        model = Profile
        fields = ["username", "name", "position", "photo", "rank"]

    def get_name(self, obj):
        return obj.display_name


class SelfProfileSerializer(serializers.ModelSerializer):
    """Used by /accounts/me/ — a user editing their OWN profile can change
    their photo, name, and username, but never their own position (that's
    fixed hierarchy, only changeable by a higher-ranked account via
    /accounts/users/<id>/)."""
    username = serializers.CharField(source="user.username")
    name = serializers.SerializerMethodField()
    rank = serializers.IntegerField(read_only=True)
    position = serializers.CharField(read_only=True)

    class Meta:
        model = Profile
        fields = ["username", "name", "position", "photo", "rank"]

    def get_name(self, obj):
        return obj.display_name

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username can't be blank.")
        taken = User.objects.filter(username=value).exclude(pk=self.instance.user_id).exists()
        if taken:
            raise serializers.ValidationError("That username is already taken.")
        return value

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", None)
        if user_data and "username" in user_data:
            instance.user.username = user_data["username"]
            instance.user.save(update_fields=["username"])
        return super().update(instance, validated_data)


class AccountUpdateSerializer(serializers.ModelSerializer):
    """Used by the Accounts page when a higher-ranked user edits someone
    else's position. View-level permission (accounts/views.py) enforces the
    actual hierarchy rule; this serializer just validates the choice itself."""

    class Meta:
        model = Profile
        fields = ["position"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class RegisterSerializer(serializers.Serializer):
    """Used by admins/scripts to create a new login — not exposed on the
    sign-in screen itself (there's no public self-signup flow yet)."""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    name = serializers.CharField(required=False, allow_blank=True)
    position = serializers.ChoiceField(choices=Profile.Position.choices, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value

    def create(self, validated_data):
        name = validated_data.pop("name", "").strip()
        position = validated_data.pop("position", "").strip()
        first, _, last = name.partition(" ")
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            first_name=first,
            last_name=last,
        )
        Profile.objects.create(user=user, position=position)
        return user
